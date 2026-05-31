# 在 Windows Terminal 中分屏打开 Build + Review 双终端
wt -d E:\Code\Py\new\ariel split-pane -H `
  powershell -NoExit -Command "opencode --agent build" `; `
  -d E:\Code\Py\new\ariel `
  powershell -NoExit -Command "opencode --agent review"