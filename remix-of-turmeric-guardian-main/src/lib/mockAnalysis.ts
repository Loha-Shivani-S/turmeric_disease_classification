export interface AnalysisResult {
  isTurmeric: boolean;
  growthStatus: "proper" | "underdeveloped" | "overgrown";
  segmentationApplied: boolean;
  disease: string; // "Dry Leaf" | "Healthy Leaf" | "Leaf Blotch" | "Rhizome Rot" | "Leaf Spot" | "Healthy Rhizome" | "Aphids"
  confidence: number;
  remedy: string;
  locationInsight: string;
}

const remedies: Record<string, string> = {
  "Dry Leaf": "💧 Water the plant twice daily (morning & evening). Spread dry grass/straw (mulch) around the base to keep soil moist. Mix 1 handful of cow dung in 5 litres water and pour around the roots once a week. Avoid watering during peak afternoon heat.",
  "Healthy Leaf": "✅ Your plant is healthy! Keep watering regularly. Add cow dung compost or vermicompost once every 2 weeks. Remove weeds around the plant. Check leaves every 3-4 days for any spots or yellowing.",
  "Leaf Blotch": "🍂 Pluck and burn the spotted/diseased leaves immediately. Mix 50g turmeric powder + 1 litre buttermilk, spray on remaining leaves. Alternatively, dissolve 10g baking soda (meetha soda) in 1 litre water and spray every 5 days. Ensure plants are not too close together for air flow. Sprinkle wood ash (chulha ki raakh) around the base.",
  "Leaf Spot": "🍂 Pluck and burn the spotted/diseased leaves immediately. Ensure the plants have enough spacing for airflow. Spray Neem oil mixed with water once a week.",
  "Rhizome Rot": "🚨 Stop watering immediately for 2-3 days. Dig a small drain channel around the plant to remove standing water. Mix neem cake (neem ki khali) into the soil around the plant. Apply a paste of turmeric powder + cow urine around the base. If the rot has spread, remove the affected rhizome, dry it in sun, and replant in raised bed with good drainage.",
  "Healthy Rhizome": "✅ The rhizome is perfectly healthy! Make sure to keep the soil well-drained to prevent any future rot.",
  "Aphids": "🐛 Spray the plant with a strong stream of water to dislodge the bugs. You can also spray a mixture of neem oil and mild dish soap to safely eliminate the pests.",
};

const locationDetails: Record<string, { soil: string; climate: string; bestPractice: string }> = {
  tropical: {
    soil: "Red laterite / alluvial soil — rich in iron, good for turmeric",
    climate: "Hot & humid — high rainfall area",
    bestPractice: "Plant in raised beds (6-8 inches high) to prevent waterlogging. Use shade nets during extreme heat. Best planting time: May-June with onset of monsoon.",
  },
  subtropical: {
    soil: "Loamy / clay-loam soil — moderate fertility",
    climate: "Warm with seasonal rains",
    bestPractice: "Ensure proper drainage channels between rows. Add organic compost before planting. Harvest after 8-9 months when leaves start drying.",
  },
  temperate: {
    soil: "Sandy loam — needs organic matter addition",
    climate: "Moderate temperature — lower humidity",
    bestPractice: "Grow in containers or greenhouses if temperature drops below 15°C. Water less frequently but deeply. Add cow dung compost monthly.",
  },
};

export function getLocationInsight(lat: number, lon: number): string {
  const zone = lat > 20 ? "tropical" : lat > 10 ? "subtropical" : "temperate";
  const details = locationDetails[zone];
  return `📍 Zone: ${zone.charAt(0).toUpperCase() + zone.slice(1)} (${lat.toFixed(2)}°N, ${lon.toFixed(2)}°E)\n🌱 Soil Type: ${details.soil}\n🌤️ Climate: ${details.climate}\n👨‍🌾 Tip: ${details.bestPractice}`;
}

// ─────────────────────────────────────────────────────────────
// Groq AI — Ultra-fast LPU model (llama-3.1-8b-instant ~200ms)
// ─────────────────────────────────────────────────────────────
async function getGrokInsights(
  disease: string,
  lat?: number,
  lon?: number
): Promise<{ remedy: string; locationInsight: string } | null> {
  const apiKey = import.meta.env.VITE_GROQ_API_KEY;
  if (!apiKey || apiKey === "your_groq_api_key_here") return null;

  const locationCtx = lat !== undefined && lon !== undefined
    ? `The farmer's exact GPS location is ${lat.toFixed(4)}°N, ${lon.toFixed(4)}°E.`
    : "No GPS location was provided. Give general advice for Indian turmeric farmers.";

  const prompt = `You are TurmeriCare AI, an expert agricultural assistant specialized in turmeric farming in India.

A turmeric plant has been diagnosed with: "${disease}".
${locationCtx}

Respond with ONLY a valid JSON object in this format:
{
  "remedy": "Practical 2-3 sentence organic remedy with emojis.",
  "locationInsight": "📍 Region | 🌡️ Climate | 🌱 Soil | 👨‍🌾 Local Tip"
}`;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 1500); // 1.5s max

  try {
    const response = await fetch("https://api.groq.com/openai/v1/chat/completions", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${apiKey}`,
      },
      signal: controller.signal,
      body: JSON.stringify({
        model: "llama-3.1-8b-instant",
        messages: [{ role: "user", content: prompt }],
        temperature: 0.5,
        max_tokens: 220,
      }),
    });
    clearTimeout(timeoutId);

    if (!response.ok) throw new Error(`Groq API error: ${response.status}`);

    const data = await response.json();
    const text = data.choices?.[0]?.message?.content ?? "";
    const clean = text.replace(/```json|```/g, "").trim();
    return JSON.parse(clean);
  } catch (err) {
    clearTimeout(timeoutId);
    console.warn("Groq API timed out or failed, using instant local fallback:", err);
    return null;
  }
}

export async function runMockAnalysis(
  imageFile: File,
  lat?: number,
  lon?: number
): Promise<AnalysisResult> {
  let disease = "Healthy Leaf";
  let confidence = 0.95;

  const hfBaseUrl = "https://loni-lolita-turmericare-backend.hf.space";
  const hfToken = import.meta.env.VITE_HF_TOKEN;

  const authHeaders: Record<string, string> = hfToken ? { "Authorization": `Bearer ${hfToken}` } : {};

  try {
    // 1. Upload file to Gradio upload endpoint
    const uploadFormData = new FormData();
    uploadFormData.append('files', imageFile);

    const uploadRes = await fetch(`${hfBaseUrl}/gradio_api/upload`, {
      method: 'POST',
      headers: { ...authHeaders },
      body: uploadFormData,
    });

    if (uploadRes.ok) {
      const uploadData = await uploadRes.json();
      const uploadedFilePath = uploadData[0];

      // 2. Call prediction event
      const eventRes = await fetch(`${hfBaseUrl}/gradio_api/call/predict`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeaders },
        body: JSON.stringify({
          data: [{ path: uploadedFilePath, meta: { _type: 'gradio.FileData' } }]
        }),
      });

      const { event_id } = await eventRes.json();

      // 3. Fetch SSE result
      const streamRes = await fetch(`${hfBaseUrl}/gradio_api/call/predict/${event_id}`, {
        headers: { ...authHeaders }
      });
      const streamText = await streamRes.text();

      // Parse SSE stream response natively
      const lines = streamText.split('\n');
      for (const line of lines) {
        if (line.startsWith('data:')) {
          const jsonPayload = line.substring(5).trim();
          try {
            const arrayData = JSON.parse(jsonPayload);
            if (Array.isArray(arrayData) && arrayData[0]) {
              const item = typeof arrayData[0] === 'string' ? JSON.parse(arrayData[0]) : arrayData[0];
              if (item && item.disease) {
                disease = item.disease;
                confidence = item.confidence ?? confidence;
                console.log("✓ Live AI Prediction Parsed Successfully:", disease, confidence);
                break;
              }
            }
          } catch (e) {
            // Continuation line
          }
        }
      }
    }
  } catch (error) {
    console.error("Backend AI server call error:", error);
  }

  // Fetch Groq LPU remedy & location insights (~200ms ultra-fast inference)
  const grok = await getGrokInsights(disease, lat, lon);

  const remedy = grok?.remedy ?? remedies[disease] ?? "Continue regular care and monitoring.";
  const locationInsight = grok?.locationInsight ?? (
    lat !== undefined && lon !== undefined
      ? getLocationInsight(lat, lon)
      : "Location not available. Enable GPS for environmental insights."
  );

  return {
    isTurmeric: true,
    growthStatus: ["proper", "underdeveloped", "overgrown"][
      Math.floor(Math.random() * 3)
    ] as AnalysisResult["growthStatus"],
    segmentationApplied: true,
    disease,
    confidence: Math.round(confidence * 100) / 100,
    remedy,
    locationInsight,
  };
}

export interface HistoryRecord {
  id: string;
  imageUrl: string;
  prediction: string;
  confidence: number;
  growthStatus: string;
  location: { lat: number; lon: number } | null;
  timestamp: string;
  remedy: string;
}
