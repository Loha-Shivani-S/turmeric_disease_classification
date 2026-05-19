import { motion } from "framer-motion";
import { Camera, MapPin, Brain, Pill, History, Shield } from "lucide-react";

const features = [
  {
    icon: Camera,
    title: "Smart Capture",
    desc: "Upload or use your camera to capture turmeric plant images instantly.",
    gradient: "from-primary/20 to-accent/20",
  },
  {
    icon: Brain,
    title: "AI Pipeline",
    desc: "4-stage analysis: detection, growth check, segmentation, and classification.",
    gradient: "from-accent/20 to-leaf/20",
  },
  {
    icon: MapPin,
    title: "Location Aware",
    desc: "Auto-detect location for environmental insights and risk assessment.",
    gradient: "from-turmeric/20 to-primary/20",
  },
  {
    icon: Pill,
    title: "Remedy System",
    desc: "Get specific treatment recommendations for each detected disease.",
    gradient: "from-leaf/20 to-turmeric/20",
  },
  {
    icon: History,
    title: "History Tracking",
    desc: "Track all your scans with full analysis details over time.",
    gradient: "from-primary/20 to-turmeric/20",
  },
  {
    icon: Shield,
    title: "Secure Auth",
    desc: "Your data stays private with secure authentication and storage.",
    gradient: "from-accent/20 to-primary/20",
  },
];

const FeaturesSection = () => (
  <section id="features" className="py-24 relative overflow-hidden">
    {/* Background glow */}
    <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[600px] rounded-full bg-primary/5 blur-[150px]" />

    <div className="container mx-auto px-4 relative z-10">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        className="text-center mb-16"
      >
        <span className="text-primary text-sm font-mono tracking-wider uppercase mb-3 block">Features</span>
        <h2 className="font-display text-4xl md:text-5xl font-bold mb-4">
          Powerful <span className="text-gradient-green">Features</span>
        </h2>
        <p className="text-muted-foreground max-w-md mx-auto">
          Everything you need to monitor and protect your turmeric crops.
        </p>
      </motion.div>

      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
        {features.map((f, i) => (
          <motion.div
            key={f.title}
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: i * 0.1 }}
            whileHover={{ scale: 1.03, y: -5 }}
            className="group cursor-default"
          >
            <div className={`p-6 rounded-2xl bg-card border border-border hover:border-primary/40 transition-all duration-500 h-full relative overflow-hidden`}>
              {/* Hover glow effect */}
              <div className="absolute inset-0 bg-gradient-to-br opacity-0 group-hover:opacity-100 transition-opacity duration-500" style={{
                background: "radial-gradient(circle at 30% 30%, hsla(145, 65%, 42%, 0.08), transparent 60%)"
              }} />

              <div className="relative z-10">
                <div className="w-14 h-14 rounded-2xl bg-primary/10 border border-primary/20 flex items-center justify-center mb-4 group-hover:glow-primary transition-all duration-500">
                  <f.icon className="w-7 h-7 text-primary" />
                </div>
                <h3 className="font-display font-semibold text-lg mb-2 text-foreground">{f.title}</h3>
                <p className="text-muted-foreground text-sm leading-relaxed">{f.desc}</p>
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  </section>
);

export default FeaturesSection;
