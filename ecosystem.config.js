const path = require("path");

module.exports = {
  apps: [
    {
      name: "azure-pricing-mcp",
      script: path.join(__dirname, ".venv", "Scripts", "python.exe"),
      args: "-m azure_pricing_mcp",
      cwd: __dirname,
      interpreter: "none",
      autorestart: true,
      watch: false,
      max_restarts: 10,
      restart_delay: 3000,
    },
  ],
};
