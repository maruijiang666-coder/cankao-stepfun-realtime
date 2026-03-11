
// tools.js

// --- Helper Functions ---

function createSuccessResponse(data) {
  const response = {
    isSuccess: true,
    error: null,
    data
  };
  console.log(`✅ Wanda工具调用成功:`, JSON.stringify(response, null, 2));
  return response;
}

function createErrorResponse(error) {
  const response = {
    isSuccess: false,
    error,
    data: null
  };
  console.log(`❌ Wanda工具调用失败:`, JSON.stringify(response, null, 2));
  return response;
}

async function fetchJson(url, params = {}) {
  const urlObj = new URL(url);
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      urlObj.searchParams.append(key, String(value));
    }
  });

  console.log(`🌐 Fetching: ${urlObj.toString()}`);
  const response = await fetch(urlObj.toString(), {
    headers: {
      'accept': 'application/json'
    }
  });

  if (!response.ok) {
    throw new Error(`API request failed with status ${response.status}: ${response.statusText}`);
  }

  return await response.json();
}

// --- Tools Definitions ---

// 1. Get Activities
const getActivitiesTool = {
  name: 'get_activities',
  description: '获取万达双塔的活动列表。可以根据特定条件筛选活动。',
  parameters: {
    type: 'object',
    properties: {
      search: {
        type: 'string',
        description: '搜索关键词，例如活动标题或内容'
      },
      page: {
        type: 'integer',
        description: '分页页码',
        default: 1
      },
      is_featured: {
        type: 'boolean',
        description: '是否为精选活动'
      },
      is_pin: {
        type: 'boolean',
        description: '是否置顶'
      },
      ordering: {
        type: 'string',
        description: '排序字段'
      }
    }
  },
  handler: async (args) => {
    console.log(`🎉 调用活动API:`, args);
    try {
      const data = await fetchJson('https://wanda.tangledup-ai.com/api/activities/activities/', args);
      return createSuccessResponse(data);
    } catch (error) {
      return createErrorResponse(error instanceof Error ? error.message : String(error));
    }
  }
};

// 2. Get Listings
const getListingsTool = {
  name: 'get_listings',
  description: '获取万达双塔的房源列表。可以查询不同楼层、区域的房源信息。',
  parameters: {
    type: 'object',
    properties: {
      search: {
        type: 'string',
        description: '搜索关键词'
      },
      page: {
        type: 'integer',
        description: '分页页码',
        default: 1
      },
      location__floor: {
        type: 'integer',
        description: '楼层'
      },
      location__unit: {
        type: 'string',
        description: '单元号'
      },
      location__zone: {
        type: 'string',
        description: '行政区划/楼栋。仅在用户明确指定特定楼栋时使用。可选值：公寓1栋, 公寓2栋, 公寓5栋, 北塔9栋, 南塔8栋'
      },
      ordering: {
        type: 'string',
        description: '排序字段'
      }
    }
  },
  handler: async (args) => {
    console.log(`🏠 调用房源API:`, args);
    try {
      const data = await fetchJson('https://wanda.tangledup-ai.com/api/listings/', args);
      return createSuccessResponse(data);
    } catch (error) {
      return createErrorResponse(error instanceof Error ? error.message : String(error));
    }
  }
};

// 3. Get Merchants
const getMerchantsTool = {
  name: 'get_merchants',
  description: '查询万达双塔的入驻商户信息。',
  parameters: {
    type: 'object',
    properties: {
      search: {
        type: 'string',
        description: '搜索关键词，如商户名称'
      },
      page: {
        type: 'integer',
        description: '分页页码',
        default: 1
      },
      page_size: {
        type: 'integer',
        description: '每页数量',
        default: 10
      },
      location__zone: {
        type: 'string',
        description: '行政区划/楼栋。仅在用户明确指定特定楼栋时使用。可选值：公寓1栋, 公寓2栋, 公寓5栋, 北塔9栋, 南塔8栋'
      },
      industry_type: {
        type: 'integer',
        description: '行业类型ID'
      },
      status: {
        type: 'string',
        description: '营业状态，可选值：正常营业, 暂停营业, 已停业'
      },
      approval_status: {
        type: 'string',
        description: '审核状态，可选值：pending, approved, rejected'
      },
      is_featured: {
        type: 'boolean',
        description: '是否精选'
      },
      ordering: {
        type: 'string',
        description: '排序字段'
      }
    }
  },
  handler: async (args) => {
    console.log(`🏢 调用商户API:`, args);
    try {
      const data = await fetchJson('https://wanda.tangledup-ai.com/api/merchants/', args);
      return createSuccessResponse(data);
    } catch (error) {
      return createErrorResponse(error instanceof Error ? error.message : String(error));
    }
  }
};

// 4. Get Registration
const getRegistrationTool = {
  name: 'get_registration',
  description: '通过手机号查询活动报名信息。',
  parameters: {
    type: 'object',
    properties: {
      phone_number: {
        type: 'string',
        description: '报名时使用的手机号'
      }
    },
    required: ['phone_number']
  },
  handler: async (args) => {
    console.log(`📋 调用报名查询API:`, args);
    const { phone_number } = args;
    if (!phone_number) {
      return createErrorResponse('必须提供手机号');
    }

    try {
      const url = `https://wanda.tangledup-ai.com/api/activities/registrations/ongoing/${phone_number}/`;
      console.log(`🌐 Fetching: ${url}`);
      const response = await fetch(url, {
        headers: {
          'accept': 'application/json'
        }
      });

      if (response.status === 404) {
        return createErrorResponse('您的报名信息有误');
      }

      if (!response.ok) {
        throw new Error(`API request failed with status ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      
      if (Array.isArray(data) && data.length === 0) {
        return createErrorResponse('您的报名信息有误');
      }

      return createSuccessResponse(data);
    } catch (error) {
      return createErrorResponse(error instanceof Error ? error.message : String(error));
    }
  }
};


const INDUSTRY_TYPES_MAPPING = `
### 行业类型对照表 (industry_type ID)
如果用户查询以下特定行业的商户，请优先使用对应的 industry_type ID 进行过滤，而不是仅使用 search 关键词。

| ID | 行业名称 |
|----|----------|
| 45 | 地产/建筑/工程 |
| 46 | 金融服务 |
| 47 | 食品/酒类/餐饮 |
| 48 | 酒店/酒店管理 |
| 49 | 旅游 |
| 50 | 教育/培训/咨询服务/文化 |
| 51 | 医疗/健康 |
| 52 | 美容美发 |
| 53 | 互联网科技/传媒/电商/信息技术 |
| 54 | 物流运输 |
| 55 | 电影娱乐 |
| 56 | 法律/法律咨询 (查询律所请用此ID) |
| 57 | 贸易/外贸 |
| 58 | 能源/环保 |
| 59 | 服务 |
| 60 | 其他 |
| 61 | 农业/林/畜牧/渔业/养殖类 |
| 62 | 测试行业 |
`;

const TOOL_SUMMARY = [getActivitiesTool, getListingsTool, getMerchantsTool, getRegistrationTool]
  .map(tool => {
    const params = Object.entries(tool.parameters.properties || {})
      .map(([key, schema]) => `  - ${key}: ${schema.description}`)
      .join('\n');
    return `- ${tool.name}: ${tool.description}\n${params}`;
  })
  .join('\n\n');

const WANDA_SYSTEM_PROMPT_SEGMENT = `
你现在可以访问万达双塔的实时数据，包括活动、房源和商户信息。

可用工具：
${TOOL_SUMMARY}

${INDUSTRY_TYPES_MAPPING}

# 注意事项
1. 请根据用户的意图选择合适的工具。
2. 查询特定行业商户时，必须优先检查行业类型对照表，如果匹配则使用 industry_type 参数。
3. 如果用户没有指定具体的筛选条件，可以先调用工具获取概览。
4. 可以在一次回复中调用多个工具。
5. 当工具返回多个条目时，请务必使用 Markdown 表格形式在对话框中罗列信息。
`;

module.exports = {
  getActivitiesTool,
  getListingsTool,
  getMerchantsTool,
  getRegistrationTool,
  WANDA_SYSTEM_PROMPT_SEGMENT
};
