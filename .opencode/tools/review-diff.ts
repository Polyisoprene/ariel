import { tool } from "@opencode-ai/plugin"

export default tool({
  description: "Get the current git diff for code review",
  args: {
    staged: tool.schema.boolean().optional().describe("Show staged changes only"),
  },
  async execute(args) {
    const flag = args.staged ? "--cached" : ""
    const result = await Bun.$`git diff ${flag}`.text()
    return result || "No changes detected"
  },
})