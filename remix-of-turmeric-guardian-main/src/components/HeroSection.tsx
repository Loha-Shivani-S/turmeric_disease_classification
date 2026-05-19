import { motion } from "framer-motion";
import { ArrowRight, Leaf } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import Scene3D from "@/components/Scene3D";

const HeroSection = () => {
  const navigate = useNavigate();

  const scrollToSection = (id: string) => {
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth" });
  };

  return (
    <section className="relative min-h-screen flex items-center overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-br from-background via-background to-forest" />
      <Scene3D />

      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/4 right-1/4 w-96 h-96 rounded-full bg-primary/10 blur-[120px]" />
        <div className="absolute bottom-1/3 left-1/4 w-64 h-64 rounded-full bg-turmeric/8 blur-[100px]" />
      </div>

      <div className="container mx-auto px-4 relative z-10 pt-20">
        <div className="max-w-2xl">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7 }}
          >
            <span className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-primary/15 border border-primary/30 text-primary text-sm font-medium mb-6">
              <Leaf className="w-4 h-4" />
              AI-Powered Plant Health
            </span>
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.1 }}
            className="font-display text-4xl sm:text-5xl md:text-7xl font-bold leading-tight mb-6 text-foreground"
          >
            Detect Turmeric
            <br />
            <span className="text-gradient-turmeric neon-text">Disease Instantly</span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.2 }}
            className="text-base sm:text-lg md:text-xl mb-8 max-w-lg text-muted-foreground"
          >
            Snap a photo of your turmeric plant and let our multi-stage AI
            pipeline diagnose diseases, assess growth, and recommend treatments
            — all in seconds.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.3 }}
            className="flex flex-col sm:flex-row gap-4"
          >
            <Link to="/signup">
              <Button size="lg" className="text-base px-8 glow-primary w-full sm:w-auto">
                Start Diagnosing <ArrowRight className="ml-2 w-5 h-5" />
              </Button>
            </Link>
            <Button
              variant="outline"
              size="lg"
              className="text-base px-8 border-primary/30 text-foreground hover:bg-primary/10 hover:border-primary/50 w-full sm:w-auto"
              onClick={() => scrollToSection("how-it-works")}
            >
              See How It Works
            </Button>
          </motion.div>

          {/* Stats */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.6 }}
            className="flex flex-wrap gap-4 md:gap-6 mt-10 md:mt-12"
          >
            {[
              { value: "4", label: "Disease Types" },
              { value: "95%+", label: "Accuracy" },
              { value: "<3s", label: "Analysis Time" },
            ].map((stat) => (
              <motion.div
                key={stat.label}
                whileHover={{ scale: 1.05, y: -4 }}
                className="px-4 md:px-5 py-2.5 md:py-3 rounded-xl bg-glass-light border-glow"
              >
                <div className="font-display text-xl md:text-2xl font-bold text-primary neon-text">
                  {stat.value}
                </div>
                <div className="text-[10px] md:text-xs text-muted-foreground">
                  {stat.label}
                </div>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </div>
    </section>
  );
};

export default HeroSection;
