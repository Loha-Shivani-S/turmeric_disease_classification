import { motion } from "framer-motion";
import { Search, TrendingUp, Layers, Tag } from "lucide-react";
import MiniScene3D from "@/components/MiniScene3D";

const stages = [
  {
    icon: Search,
    num: "01",
    title: "Plant Detection",
    desc: "Verify if the image contains a turmeric plant using pretrained detection model.",
    color: "text-leaf",
    borderColor: "border-leaf/30",
    bgColor: "bg-leaf/10",
  },
  {
    icon: TrendingUp,
    num: "02",
    title: "Growth Assessment",
    desc: "Classify growth stage: proper, underdeveloped, or overgrown/unhealthy.",
    color: "text-primary",
    borderColor: "border-primary/30",
    bgColor: "bg-primary/10",
  },
  {
    icon: Layers,
    num: "03",
    title: "Disease Segmentation",
    desc: "Custom U-Net architecture segments the diseased region with a binary mask.",
    color: "text-turmeric",
    borderColor: "border-turmeric/30",
    bgColor: "bg-turmeric/10",
  },
  {
    icon: Tag,
    num: "04",
    title: "Disease Classification",
    desc: "Custom MobileNet classifies: Dry Leaf, Healthy, Leaf Blotch, or Rhizome Rot.",
    color: "text-destructive",
    borderColor: "border-destructive/30",
    bgColor: "bg-destructive/10",
  },
];

const PipelineSection = () => (
  <section id="how-it-works" className="py-24 relative overflow-hidden">
    <div className="container mx-auto px-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        className="text-center mb-16"
      >
        <span className="text-primary text-sm font-mono tracking-wider uppercase mb-3 block">Architecture</span>
        <h2 className="font-display text-4xl md:text-5xl font-bold mb-4">
          AI <span className="text-gradient-turmeric">Pipeline</span>
        </h2>
        <p className="text-muted-foreground max-w-lg mx-auto">
          Four stages of analysis powered by custom-trained deep learning models.
        </p>
      </motion.div>

      <div className="grid lg:grid-cols-2 gap-12 items-center max-w-5xl mx-auto">
        {/* Left: 3D DNA visualization */}
        <motion.div
          initial={{ opacity: 0, x: -30 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true }}
          className="h-[400px] rounded-3xl overflow-hidden border border-border bg-card relative glow-green"
        >
          <MiniScene3D />
          <div className="absolute bottom-4 left-4 right-4 bg-glass rounded-xl p-3 text-center pointer-events-none">
            <p className="text-xs text-muted-foreground font-mono">Interactive Scanning Simulation: Drag to explore</p>
          </div>
        </motion.div>

        {/* Right: stages */}
        <div className="space-y-4">
          {stages.map((s, i) => (
            <motion.div
              key={s.num}
              initial={{ opacity: 0, x: 30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.12 }}
              whileHover={{ x: 8, scale: 1.02 }}
              className={`flex gap-4 items-start p-4 rounded-2xl border ${s.borderColor} bg-card hover:bg-muted/30 transition-all cursor-default`}
            >
              <div className={`w-12 h-12 rounded-xl ${s.bgColor} flex items-center justify-center flex-shrink-0`}>
                <s.icon className={`w-6 h-6 ${s.color}`} />
              </div>
              <div>
                <span className="text-[10px] font-mono text-muted-foreground tracking-wider">
                  STAGE {s.num}
                </span>
                <h3 className="font-display font-semibold text-lg text-foreground">
                  {s.title}
                </h3>
                <p className="text-muted-foreground text-sm mt-0.5">{s.desc}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  </section>
);

export default PipelineSection;
