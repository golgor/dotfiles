return {
  {
    "mason-org/mason.nvim",
    opts = { ensure_installed = { "tofu-ls" } },
  },

  {
    "neovim/nvim-lspconfig",
    opts = {
      servers = {
        -- Use OpenTofu's language server instead of HashiCorp terraform-ls.
        terraformls = { enabled = false },
        tofu_ls = {},

        -- Run TFLint through mise so the LSP uses the project's configured
        -- tflint version instead of Mason's binary.
        tflint = {
          cmd = { "mise", "x", "--", "tflint", "--langserver" },
        },
      },
    },
  },

  -- LazyVim's Terraform extra defaults to `terraform fmt`; use `tofu fmt`.
  {
    "stevearc/conform.nvim",
    opts = {
      formatters_by_ft = {
        terraform = { "tofu_fmt" },
        tf = { "tofu_fmt" },
        ["terraform-vars"] = { "tofu_fmt" },
        opentofu = { "tofu_fmt" },
        ["opentofu-vars"] = { "tofu_fmt" },
      },
    },
  },

  -- LazyVim's Terraform extra defaults to `terraform validate`; use `tofu validate`.
  {
    "mfussenegger/nvim-lint",
    opts = {
      linters_by_ft = {
        terraform = { "tofu" },
        tf = { "tofu" },
        opentofu = { "tofu" },
        ["opentofu-vars"] = { "tofu" },
      },
    },
  },
}
