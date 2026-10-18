import "./globals.css";

export const metadata = {
  title: "QuantPulse",
  description: "Market monitor and AI assistant",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className="bg-slate-950 text-slate-100 antialiased">{children}</body>
    </html>
  );
}