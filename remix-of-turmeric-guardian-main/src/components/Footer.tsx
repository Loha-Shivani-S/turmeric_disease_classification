import { Leaf } from "lucide-react";
import { Link } from "react-router-dom";

const Footer = () => (
  <footer className="py-12 border-t border-border relative overflow-hidden">
    {/* Subtle glow */}
    <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-96 h-32 bg-primary/5 blur-[80px]" />

    <div className="container mx-auto px-4 relative z-10">
      <div className="flex flex-col md:flex-row items-center justify-between gap-4">
        <Link to="/" className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-primary/15 border border-primary/25 flex items-center justify-center">
            <Leaf className="w-4 h-4 text-primary" />
          </div>
          <span className="font-display font-bold text-gradient-turmeric">TurmeriCare</span>
        </Link>
        <p className="text-sm text-muted-foreground">
          © 2026 TurmeriCare. AI-powered turmeric disease detection.
        </p>
      </div>
    </div>
  </footer>
);

export default Footer;
