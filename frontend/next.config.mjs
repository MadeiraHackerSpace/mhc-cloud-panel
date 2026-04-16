/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  transpilePackages: ['@novnc/novnc'],
  webpack: (config, { isServer }) => {
    if (!isServer) {
      // Don't resolve @novnc on server-side (SSR)
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
        net: false,
        tls: false,
      };
    }
    
    // Handle noVNC ES modules
    config.module.rules.push({
      test: /\.m?js$/,
      include: /node_modules\/@novnc/,
      type: 'javascript/auto',
      resolve: {
        fullySpecified: false,
      },
    });
    
    return config;
  },
  experimental: {
    esmExternals: 'loose',
  },
};

export default nextConfig;

