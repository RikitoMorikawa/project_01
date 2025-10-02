/** @type {import('next').NextConfig} */
const nextConfig = {
  // Disable static export for authentication features
  // output: "export", // Commented out to enable SSR for auth
  trailingSlash: true,
  images: {
    unoptimized: true,
  },
  // Disable static optimization for auth pages
  experimental: {
    esmExternals: false,
  },
  // Environment-specific configuration
  env: {
    NEXT_PUBLIC_API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL,
    NEXT_PUBLIC_AWS_REGION: process.env.NEXT_PUBLIC_AWS_REGION,
    NEXT_PUBLIC_COGNITO_USER_POOL_ID: process.env.NEXT_PUBLIC_COGNITO_USER_POOL_ID,
    NEXT_PUBLIC_COGNITO_CLIENT_ID: process.env.NEXT_PUBLIC_COGNITO_CLIENT_ID,
  },
};

module.exports = nextConfig;
