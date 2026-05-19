import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Clock, Tag, MapPin, TrendingUp, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import Navbar from "@/components/Navbar";
import { useNavigate } from "react-router-dom";
import type { HistoryRecord } from "@/lib/mockAnalysis";
import { supabase } from "@/lib/supabase";

const History = () => {
  const [records, setRecords] = useState<HistoryRecord[]>([]);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchHistory = async () => {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) {
        navigate("/login");
        return;
      }

      const { data } = await supabase
        .from('plant_history')
        .select('*')
        .order('created_at', { ascending: false });

      if (data) {
        const formatted = data.map(r => ({
          id: r.id,
          imageUrl: r.image_url,
          prediction: r.disease_name,
          confidence: r.confidence,
          timestamp: r.created_at,
          remedy: r.recommendation,
          growthStatus: 'Analyzed',
          location: null,
        }));
        setRecords(formatted);
      }
    };

    fetchHistory();
  }, [navigate]);

  const clearHistory = async () => {
    const { data: { user } } = await supabase.auth.getUser();
    if (user) {
      await supabase.from('plant_history').delete().eq('user_id', user.id);
      setRecords([]);
    }
  };

  const handleLogout = async () => {
    await supabase.auth.signOut();
    navigate("/");
  };

  return (
    <div className="min-h-screen bg-background">
      <Navbar isLoggedIn onLogout={handleLogout} />
      <div className="container mx-auto px-4 pt-24 pb-16">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="font-display text-3xl font-bold">
              Analysis <span className="text-gradient-turmeric">History</span>
            </h1>
            <p className="text-muted-foreground text-sm mt-1">
              {records.length} scan{records.length !== 1 ? "s" : ""} recorded
            </p>
          </div>
          {records.length > 0 && (
            <Button variant="outline" size="sm" onClick={clearHistory}>
              <Trash2 className="w-4 h-4 mr-1" /> Clear
            </Button>
          )}
        </div>

        {records.length === 0 ? (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center py-20"
          >
            <Clock className="w-12 h-12 text-muted-foreground/30 mx-auto mb-4" />
            <p className="text-muted-foreground">No scans yet. Go to Dashboard to analyze your first plant!</p>
            <Button className="mt-4" onClick={() => navigate("/dashboard")}>
              Start Scanning
            </Button>
          </motion.div>
        ) : (
          <div className="grid gap-4">
            {records.map((r, i) => (
              <motion.div
                key={r.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.05 }}
                className="rounded-xl border border-border bg-card p-4 flex gap-4 card-3d"
              >
                {r.imageUrl && (
                  <div className="w-20 h-20 rounded-lg overflow-hidden flex-shrink-0 bg-muted">
                    <img src={r.imageUrl} alt="Scan" className="w-full h-full object-cover" />
                  </div>
                )}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-1">
                    <div className="flex items-center gap-2">
                      <Tag className="w-4 h-4 text-turmeric" />
                      <span className="font-display font-semibold">{r.prediction}</span>
                    </div>
                    <span className="text-xs text-muted-foreground">
                      {new Date(r.timestamp).toLocaleDateString()}
                    </span>
                  </div>
                  <div className="flex flex-wrap gap-3 text-xs text-muted-foreground">
                    <span className="flex items-center gap-1">
                      Confidence: <strong className="text-primary">{(r.confidence * 100).toFixed(1)}%</strong>
                    </span>
                    <span className="flex items-center gap-1">
                      <TrendingUp className="w-3 h-3" /> {r.growthStatus}
                    </span>
                    {r.location && (
                      <span className="flex items-center gap-1">
                        <MapPin className="w-3 h-3" /> {r.location.lat.toFixed(2)}, {r.location.lon.toFixed(2)}
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-muted-foreground mt-2 truncate">
                    {r.remedy}
                  </p>
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default History;
