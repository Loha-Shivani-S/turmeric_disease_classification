import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Leaf, Mail, Lock, Eye, EyeOff } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useToast } from "@/hooks/use-toast";
import MiniScene3D from "@/components/MiniScene3D";
import { supabase } from "@/lib/supabase";

const Login = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { toast } = useToast();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    
    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password,
    });

    setLoading(false);

    if (error) {
      toast({ title: "Login Failed", description: error.message, variant: "destructive" });
    } else {
      toast({ title: "Welcome back!", description: "Login successful." });
      navigate("/dashboard");
    }
  };

  return (
    <div className="min-h-screen flex bg-background">
      {/* Left: form */}
      <div className="flex-1 flex items-center justify-center p-8 relative">
        {/* Background glow */}
        <div className="absolute top-1/3 left-1/3 w-64 h-64 bg-primary/5 rounded-full blur-[100px]" />

        <motion.div
          initial={{ opacity: 0, x: -30 }}
          animate={{ opacity: 1, x: 0 }}
          className="w-full max-w-md relative z-10"
        >
          <Link to="/" className="flex items-center gap-2 mb-8">
            <div className="w-9 h-9 rounded-lg bg-primary/15 border border-primary/30 flex items-center justify-center">
              <Leaf className="w-5 h-5 text-primary" />
            </div>
            <span className="font-display font-bold text-lg text-gradient-turmeric">
              TurmeriCare
            </span>
          </Link>

          <h1 className="font-display text-3xl font-bold mb-2 text-foreground">Welcome back</h1>
          <p className="text-muted-foreground mb-8">
            Sign in to continue your plant analysis.
          </p>

          <form onSubmit={handleLogin} className="space-y-4">
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input
                type="email"
                placeholder="Email address"
                className="pl-10 bg-card border-border focus:border-primary"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input
                type={showPw ? "text" : "password"}
                placeholder="Password"
                className="pl-10 pr-10 bg-card border-border focus:border-primary"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
              <button
                type="button"
                onClick={() => setShowPw(!showPw)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              >
                {showPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
            <Button type="submit" className="w-full glow-primary" disabled={loading}>
              {loading ? "Signing in..." : "Sign In"}
            </Button>
          </form>

          <p className="mt-6 text-center text-sm text-muted-foreground">
            Don't have an account?{" "}
            <Link to="/signup" className="text-primary font-medium hover:underline">
              Sign up
            </Link>
          </p>
        </motion.div>
      </div>

      {/* Right: 3D visual */}
      <div className="hidden lg:block flex-1 relative border-l border-border">
        <div className="absolute inset-0 bg-gradient-to-br from-card to-forest" />
        <div className="absolute inset-0">
          <MiniScene3D />
        </div>
        <div className="absolute inset-0 flex items-center justify-center">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.3 }}
            className="text-center bg-glass rounded-2xl p-8 max-w-xs"
          >
            <Leaf className="w-12 h-12 text-primary mx-auto mb-4 animate-float" />
            <h2 className="font-display text-2xl font-bold text-foreground">
              AI-Powered Protection
            </h2>
            <p className="text-muted-foreground mt-2 text-sm">
              Detect diseases before they spread across your crop.
            </p>
          </motion.div>
        </div>
      </div>
    </div>
  );
};

export default Login;
