import { useState, useRef, useCallback, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Camera,
  Upload,
  MapPin,
  Loader2,
  Search,
  TrendingUp,
  Layers,
  Tag,
  CheckCircle2,
  Pill,
  Leaf,
  X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { useToast } from "@/hooks/use-toast";
import { runMockAnalysis, type AnalysisResult } from "@/lib/mockAnalysis";
import Navbar from "@/components/Navbar";
import AnalysisLeaf3D from "@/components/AnalysisLeaf3D";
import { useNavigate } from "react-router-dom";
import { supabase } from "@/lib/supabase";

const pipelineStages = [
  { icon: Search, label: "Plant Detection", desc: "Verifying turmeric..." },
  { icon: TrendingUp, label: "Growth Assessment", desc: "Evaluating growth stage..." },
  { icon: Layers, label: "Segmentation", desc: "Mapping disease regions..." },
  { icon: Tag, label: "Classification", desc: "Identifying disease type..." },
];

const Dashboard = () => {
  const [image, setImage] = useState<string | null>(null);
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [location, setLocation] = useState<{ lat: number; lon: number } | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [currentStage, setCurrentStage] = useState(-1);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [cameraActive, setCameraActive] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const navigate = useNavigate();
  const { toast } = useToast();

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (!session) navigate("/login");
    });
  }, [navigate]);

  useEffect(() => {
    navigator.geolocation?.getCurrentPosition(
      (pos) => setLocation({ lat: pos.coords.latitude, lon: pos.coords.longitude }),
      () => toast({ title: "Location unavailable", description: "Enable GPS for environmental insights.", variant: "destructive" })
    );
  }, [toast]);

  const handleFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (cameraActive) stopCamera();
    const f = e.target.files?.[0];
    if (!f) return;
    setImageFile(f);
    setImage(URL.createObjectURL(f));
    setResult(null);
  };

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: { ideal: "environment" }, width: { ideal: 1280 }, height: { ideal: 720 } }
      });
      streamRef.current = stream;
      setCameraActive(true); // render the <video> first, then attach in useEffect
    } catch (err) {
      console.error("Camera error:", err);
      toast({ title: "Camera error", description: "Could not access camera. Please check permissions.", variant: "destructive" });
    }
  };

  // Attach stream to <video> after it mounts in the DOM
  useEffect(() => {
    if (cameraActive && videoRef.current && streamRef.current) {
      videoRef.current.srcObject = streamRef.current;
      videoRef.current.play().catch(console.error);
    }
  }, [cameraActive]);

  const stopCamera = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
    if (videoRef.current) videoRef.current.srcObject = null;
    setCameraActive(false);
  }, []);

  const capturePhoto = useCallback(() => {
    if (!videoRef.current || !canvasRef.current) return;
    const v = videoRef.current;
    const c = canvasRef.current;
    c.width = v.videoWidth;
    c.height = v.videoHeight;
    c.getContext("2d")?.drawImage(v, 0, 0);
    c.toBlob((blob) => {
      if (!blob) return;
      const file = new File([blob], "capture.jpg", { type: "image/jpeg" });
      setImageFile(file);
      setImage(URL.createObjectURL(blob));
      stopCamera();
      setResult(null);
    }, "image/jpeg");
  }, [stopCamera]);

  const analyze = async () => {
    if (!imageFile) return;
    setAnalyzing(true);
    setResult(null);

    for (let i = 0; i < 4; i++) {
      setCurrentStage(i);
      await new Promise((r) => setTimeout(r, 800));
    }

    const res = await runMockAnalysis(imageFile, location?.lat, location?.lon);
    setResult(res);
    setAnalyzing(false);
    setCurrentStage(-1);

    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) return;

      let publicUrl = null;
      if (imageFile) {
        const fileExt = imageFile.name.split('.').pop() || 'jpg';
        const fileName = `${user.id}-${Date.now()}.${fileExt}`;
        const { error: uploadError } = await supabase.storage
          .from('plant_images')
          .upload(fileName, imageFile);

        if (!uploadError) {
          const { data } = supabase.storage.from('plant_images').getPublicUrl(fileName);
          publicUrl = data.publicUrl;
        } else {
          console.error("Image upload error:", uploadError);
        }
      }

      const { error: dbError } = await supabase.from('plant_history').insert({
        user_id: user.id,
        image_url: publicUrl,
        disease_name: res.disease,
        confidence: res.confidence,
        recommendation: res.remedy,
      });

      if (dbError) {
        console.error("Database insert error:", dbError);
      }
    } catch (err) {
      console.error("Error saving history:", err);
    }
  };

  const handleLogout = async () => {
    await supabase.auth.signOut();
    navigate("/");
  };

  const diseaseColorMap: Record<string, string> = {
    "Dry Leaf": "text-turmeric-dark",
    "Healthy Leaf": "text-primary",
    "Leaf Blotch": "text-earth-light",
    "Leaf Spot": "text-earth-light",
    "Rhizome Rot": "text-destructive",
    "Healthy Rhizome": "text-primary",
    "Aphids": "text-destructive",
  };

  return (
    <div className="min-h-screen bg-background">
      <Navbar isLoggedIn onLogout={handleLogout} />
      <div className="container mx-auto px-4 pt-24 pb-16">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-8 md:mb-10"
        >
          <h1 className="font-display text-3xl md:text-4xl font-bold mb-2">
            Analyze Your <span className="text-gradient-turmeric">Turmeric</span>
          </h1>
          <p className="text-muted-foreground text-sm md:text-base">
            Upload or capture an image to start the AI analysis pipeline.
          </p>
          {location && (
            <div className="inline-flex items-center gap-1 mt-3 text-sm text-muted-foreground bg-card px-3 py-1 rounded-full border border-border">
              <MapPin className="w-3 h-3 text-primary" />
              {location.lat.toFixed(4)}, {location.lon.toFixed(4)}
            </div>
          )}
        </motion.div>

        <div className="grid lg:grid-cols-2 gap-6 md:gap-8 max-w-5xl mx-auto">
          {/* Left: Image capture */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 }}
          >
            <div className="rounded-2xl border border-border bg-card overflow-hidden">
              <div className="aspect-[4/3] relative bg-muted flex items-center justify-center">
                {cameraActive ? (
                  <>
                    <video ref={videoRef} autoPlay playsInline className="w-full h-full object-cover" />
                    <button
                      onClick={stopCamera}
                      className="absolute top-3 right-3 w-8 h-8 rounded-full bg-foreground/50 flex items-center justify-center text-background hover:bg-foreground/70 transition-colors z-10"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </>
                ) : image ? (
                  <>
                    <img src={image} alt="Captured" className="w-full h-full object-cover" />
                    {analyzing && (
                      <div className="absolute inset-0 bg-foreground/30 flex items-center justify-center">
                        <div className="absolute left-0 right-0 h-0.5 bg-primary animate-scan-line" />
                      </div>
                    )}
                    <button
                      onClick={() => { setImage(null); setImageFile(null); setResult(null); }}
                      className="absolute top-3 right-3 w-8 h-8 rounded-full bg-foreground/50 flex items-center justify-center text-background hover:bg-foreground/70 transition-colors"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </>
                ) : (
                  <div className="text-center p-8">
                    <Leaf className="w-12 h-12 text-muted-foreground/30 mx-auto mb-3" />
                    <p className="text-muted-foreground text-sm">
                      Upload or capture a turmeric plant image
                    </p>
                  </div>
                )}
              </div>
              <canvas ref={canvasRef} className="hidden" />
              <div className="p-3 md:p-4 flex gap-2 md:gap-3">
                <input ref={fileRef} type="file" accept="image/*" className="hidden" onChange={handleFile} />
                {cameraActive ? (
                  <>
                    <Button variant="outline" className="flex-1 text-xs md:text-sm" onClick={stopCamera}>
                      <X className="w-4 h-4 mr-1 md:mr-2" /> Cancel
                    </Button>
                    <Button className="flex-1 text-xs md:text-sm" onClick={capturePhoto}>
                      <Camera className="w-4 h-4 mr-1 md:mr-2" /> Capture
                    </Button>
                  </>
                ) : (
                  <>
                    <Button
                      variant="outline"
                      className="flex-1 text-xs md:text-sm"
                      onClick={() => fileRef.current?.click()}
                    >
                      <Upload className="w-4 h-4 mr-1 md:mr-2" /> Upload
                    </Button>
                    <Button variant="outline" className="flex-1 text-xs md:text-sm" onClick={startCamera}>
                      <Camera className="w-4 h-4 mr-1 md:mr-2" /> Camera
                    </Button>
                  </>
                )}
              </div>
              {image && !analyzing && (
                <div className="px-3 md:px-4 pb-3 md:pb-4">
                  <Button className="w-full glow-primary" onClick={analyze}>
                    Start AI Analysis
                  </Button>
                </div>
              )}
            </div>
          </motion.div>

          {/* Right: Pipeline, 3D Leaf & Results */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
            className="space-y-6"
          >
            {/* 3D Leaf visualization */}
            <div className="rounded-2xl border border-border bg-card overflow-hidden relative h-[200px] md:h-[240px]">
              <AnalysisLeaf3D analyzing={analyzing} />
              <div className="absolute bottom-3 left-3 right-3 bg-glass rounded-xl px-3 py-2 text-center">
                <p className="text-xs text-muted-foreground font-mono">
                  {analyzing ? "🔬 Scanning in progress..." : result ? "✅ Analysis complete" : "🌿 Ready for analysis"}
                </p>
              </div>
            </div>

            {/* Pipeline stages */}
            <div className="rounded-2xl border border-border bg-card p-4 md:p-6">
              <h3 className="font-display font-semibold text-base md:text-lg mb-3 md:mb-4">AI Pipeline</h3>
              <div className="space-y-2 md:space-y-3">
                {pipelineStages.map((s, i) => {
                  const done = analyzing ? i < currentStage : result ? true : false;
                  const active = analyzing && i === currentStage;
                  return (
                    <div
                      key={s.label}
                      className={`flex items-center gap-3 p-2.5 md:p-3 rounded-xl border transition-all ${
                        active
                          ? "border-primary bg-primary/5 glow-primary"
                          : done
                          ? "border-primary/30 bg-primary/5"
                          : "border-border bg-background"
                      }`}
                    >
                      <div
                        className={`w-8 h-8 md:w-10 md:h-10 rounded-lg flex items-center justify-center flex-shrink-0 ${
                          active
                            ? "bg-primary text-primary-foreground"
                            : done
                            ? "bg-primary/20 text-primary"
                            : "bg-muted text-muted-foreground"
                        }`}
                      >
                        {active ? (
                          <Loader2 className="w-4 h-4 md:w-5 md:h-5 animate-spin" />
                        ) : done ? (
                          <CheckCircle2 className="w-4 h-4 md:w-5 md:h-5" />
                        ) : (
                          <s.icon className="w-4 h-4 md:w-5 md:h-5" />
                        )}
                      </div>
                      <div>
                        <div className="font-medium text-xs md:text-sm">{s.label}</div>
                        <div className="text-[10px] md:text-xs text-muted-foreground">
                          {active ? s.desc : done ? "Complete" : "Pending"}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Results */}
            <AnimatePresence>
              {result && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  className="space-y-4"
                >
                  <div className="rounded-2xl border border-border bg-card p-4 md:p-6">
                    <h3 className="font-display font-semibold text-base md:text-lg mb-3 md:mb-4 flex items-center gap-2">
                      <Tag className="w-5 h-5 text-turmeric" /> Diagnosis
                    </h3>
                    <div className="grid grid-cols-2 gap-3 md:gap-4">
                      <div>
                        <p className="text-xs text-muted-foreground mb-1">Disease</p>
                        <p className={`font-display font-bold text-lg md:text-xl ${diseaseColorMap[result.disease] || "text-foreground"}`}>
                          {result.disease}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-muted-foreground mb-1">Confidence</p>
                        <p className="font-display font-bold text-lg md:text-xl text-primary">
                          {(result.confidence * 100).toFixed(1)}%
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-muted-foreground mb-1">Growth Status</p>
                        <span className={`inline-flex items-center gap-1 text-xs md:text-sm font-medium px-2 py-0.5 rounded-full ${
                          result.growthStatus === "proper"
                            ? "bg-primary/10 text-primary"
                            : "bg-turmeric/10 text-turmeric-dark"
                        }`}>
                          <TrendingUp className="w-3 h-3" />
                          {result.growthStatus}
                        </span>
                      </div>
                      <div>
                        <p className="text-xs text-muted-foreground mb-1">Segmentation</p>
                        <span className="text-xs md:text-sm text-primary font-medium">✓ Mask Applied</span>
                      </div>
                    </div>
                  </div>

                  <div className="rounded-2xl border border-border bg-card p-4 md:p-6">
                    <h3 className="font-display font-semibold text-base md:text-lg mb-3 flex items-center gap-2">
                      <Pill className="w-5 h-5 text-leaf" /> Remedy
                    </h3>
                    <p className="text-sm text-foreground leading-relaxed">{result.remedy}</p>
                  </div>

                  <div className="rounded-2xl border border-border bg-card p-4 md:p-6">
                    <h3 className="font-display font-semibold text-base md:text-lg mb-3 flex items-center gap-2">
                      <MapPin className="w-5 h-5 text-turmeric" /> Location & Environment
                    </h3>
                    {result.locationInsight.split("\n").map((line, i) => (
                      <p key={i} className="text-sm text-foreground leading-relaxed mb-1">
                        {line}
                      </p>
                    ))}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
