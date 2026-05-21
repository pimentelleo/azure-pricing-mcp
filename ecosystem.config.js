module.exports = {
  apps: [
    {
      name: "azure-pricing-mcp",
      script: "uv",
      args: "run azure-pricing-mcp",
      cwd: __dirname,
      interpreter: "none",
      autorestart: true,
      watch: false,
      max_restarts: 10,
      restart_delay: 3000,
      env: {
        UV_PROJECT_ENVIRONMENT: ".venv",
      },
    },
  ],
};
