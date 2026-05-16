import type { Metadata } from "next";
import "./globals.css";
import { ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import Navbar from "@/components/ui/Navbar";
import TickerTape from "@/components/ui/TickerTape";

export const metadata: Metadata = {
  title: "Alpha Station v6.0 — Institutional Quantitative Terminal",
  description: "Institutional-grade quantitative workstation for detecting exponential growth",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className="dark">
      <body className="bg-background min-h-screen font-sans antialiased text-text-primary selection:bg-electric-blue/30 selection:text-white">
        <TickerTape />
        <Navbar />
        <main className="pt-32">{children}</main>
        <ToastContainer
          position="bottom-right"
          autoClose={5000}
          hideProgressBar={false}
          newestOnTop
          closeOnClick
          pauseOnFocusLoss
          draggable
          pauseOnHover
          theme="dark"
          toastClassName="glass"
        />
      </body>
    </html>
  );
}
