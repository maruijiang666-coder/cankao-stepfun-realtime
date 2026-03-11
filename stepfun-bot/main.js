
const { RealtimeClient, ServerEventType } = require("stepfun-realtime-api");
const readline = require("readline");
const {
  getActivitiesTool,
  getListingsTool,
  getMerchantsTool,
  getRegistrationTool,
  WANDA_SYSTEM_PROMPT_SEGMENT
} = require("./tools");

// Check for API Key
if (!process.env.STEP_SECRET) {
  console.error("❌ 请设置环境变量 STEP_SECRET");
  console.error("例如 (Windows PowerShell): $env:STEP_SECRET='your_key'; node main.js");
  console.error("例如 (CMD): set STEP_SECRET=your_key && node main.js");
  process.exit(1);
}

// Initialize Client
const client = new RealtimeClient({
  url: "wss://api.stepfun.com/v1/realtime",
  secret: process.env.STEP_SECRET,
});

// Tool Map
const tools = {
  [getActivitiesTool.name]: getActivitiesTool,
  [getListingsTool.name]: getListingsTool,
  [getMerchantsTool.name]: getMerchantsTool,
  [getRegistrationTool.name]: getRegistrationTool,
};

// Add tools to client
Object.values(tools).forEach(tool => {
  client.addTool({
    type: "function",
    function: {
      name: tool.name,
      description: tool.description,
      parameters: tool.parameters,
    },
  });
});

// Setup Readline
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

function promptUser() {
  rl.question("\n👤 你: ", (input) => {
    if (!input) {
      promptUser();
      return;
    }
    if (input.toLowerCase() === 'exit') {
      console.log("👋 再见！");
      client.disconnect();
      process.exit(0);
    }
    
    // Send user message
    client.sendUserMessage([{ type: "text", text: input }]);
  });
}

// Handle Events
client.on(ServerEventType.ResponseContentPartDone, (event) => {
  if (event.part.type === "text") {
    console.log(`🤖 AI: ${event.part.text}`);
  } else if (event.part.type === "audio") {
    console.log(`🤖 AI (语音): [音频内容] ${event.part.transcript || ''}`);
  }
});

client.on(ServerEventType.ResponseFunctionCallArgumentsDone, async (event) => {
  // Check if properties are on event or event.item (handling potential SDK discrepancies)
  let name, call_id, argsString;
  
  if (event.name && event.call_id) {
    ({ name, call_id, arguments: argsString } = event);
  } else if (event.item && event.item.name) {
    ({ name, call_id, arguments: argsString } = event.item);
  } else {
    console.error("❌ 无法解析工具调用事件:", JSON.stringify(event));
    return;
  }

  const tool = tools[name];
  
  if (tool) {
    console.log(`🛠️ 调用工具: ${name}`);
    try {
      const args = JSON.parse(argsString);
      const result = await tool.handler(args);
      
      // Send result back to model
      client.sendToolResult(call_id, JSON.stringify(result));
      
      // Trigger response generation
      client.createResponse();
    } catch (error) {
      console.error(`❌ 工具调用错误:`, error);
      client.sendToolResult(call_id, JSON.stringify({ error: error.message }));
      client.createResponse();
    }
  } else {
    console.error(`❌ 未知工具: ${name}`);
  }
});

// Optional: Handle ResponseDone to re-prompt
client.on(ServerEventType.ResponseDone, (event) => {
  // Only prompt if we are not waiting for tool execution or other parts
  // But ResponseDone is for the whole response.
  // If a tool was called, we might get ResponseDone for the function call turn,
  // then we call createResponse(), and get another ResponseDone.
  
  // A simple heuristic: if the response didn't contain a function call, or if it's the final answer.
  // Actually, let's just prompt always, user can type anytime.
  // But to be cleaner, maybe we wait.
  
  // Check if response had function calls
  const hasFunctionCall = event.response.output.some(item => item.type === 'function_call');
  if (!hasFunctionCall) {
    promptUser();
  }
});

async function main() {
  try {
    await client.connect();
    console.log("✅ 已连接到 Stepfun Realtime API");
    
    // Set System Prompt
    await client.updateSession({
      instructions: `你是一个智能助手。${WANDA_SYSTEM_PROMPT_SEGMENT}`,
      voice: "qingchunshaonv" // Optional
    });

    console.log("🚀 系统准备就绪。请输入你的问题 (输入 'exit' 退出):");
    promptUser();
  } catch (error) {
    console.error("❌ 连接失败:", error);
    process.exit(1);
  }
}

main();
