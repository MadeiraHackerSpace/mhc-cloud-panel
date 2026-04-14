import type { ReactNode } from "react";
import { ThemeProvider } from "@/components/theme-provider";
import "@/styles/globals.css";

export const metadata = {
  title: "MHC Cloud Panel",
  description: "Painel de VPS para membros do MHC"
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="pt-BR" suppressHydrationWarning>
      <body>
        <ThemeProvider>{children}</ThemeProvider>
      </body>
    </html>
  );
}

