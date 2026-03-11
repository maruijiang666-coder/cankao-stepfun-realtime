import aiohttp
import json
import urllib.parse

# --- Helper Functions ---

async def fetch_json(url: str, params: dict = None):
    if params is None:
        params = {}
    
    # Filter out None values
    clean_params = {k: v for k, v in params.items() if v is not None}
    
    async with aiohttp.ClientSession() as session:
        print(f"🌐 Fetching: {url} with params {clean_params}")
        async with session.get(url, params=clean_params, headers={'accept': 'application/json'}) as response:
            if response.status != 200:
                raise Exception(f"API request failed with status {response.status}: {response.reason}")
            return await response.json()

def create_success_response(data):
    response = {
        "isSuccess": True,
        "error": None,
        "data": data
    }
    print(f"✅ Wanda工具调用成功: {json.dumps(response, indent=2, ensure_ascii=False)}")
    return json.dumps(response, ensure_ascii=False)

def create_error_response(error):
    response = {
        "isSuccess": False,
        "error": str(error),
        "data": None
    }
    print(f"❌ Wanda工具调用失败: {json.dumps(response, indent=2, ensure_ascii=False)}")
    return json.dumps(response, ensure_ascii=False)

# --- Tools Definitions ---

# 1. Get Activities
get_activities_tool = {
    "type": "function",
    "function": {
        "name": "get_activities",
        "description": "获取万达双塔的活动列表。默认获取未过期的活动。如果需要查询历史活动，请指定 scope 参数。",
        "parameters": {
            "type": "object",
            "properties": {
                "scope": {
                    "type": "string",
                    "enum": ["unexpired", "all"],
                    "default": "unexpired",
                    "description": "默认为 'unexpired' (未过期活动)。仅在用户明确询问'历史活动'、'过期活动'或'往期活动'时设置为 'all'。"
                },
                "search": {
                    "type": "string",
                    "description": "搜索关键词，例如活动标题或内容"
                },
                "page": {
                    "type": "integer",
                    "description": "分页页码",
                    "default": 1
                },
                "is_featured": {
                    "type": "boolean",
                    "description": "是否为精选活动"
                },
                "is_pin": {
                    "type": "boolean",
                    "description": "是否置顶"
                },
                "ordering": {
                    "type": "string",
                    "description": "排序字段"
                }
            }
        }
    }
}

async def get_activities_handler(args):
    print(f"🎉 调用活动API: {args}")
    scope = args.get('scope', 'unexpired')
    
    # Clean up args for API call
    api_params = args.copy()
    if 'scope' in api_params:
        del api_params['scope']

    try:
        if scope == 'all':
            data = await fetch_json('https://wanda.tangledup-ai.com/api/activities/activities/', api_params)
        else:
            data = await fetch_json('https://wanda.tangledup-ai.com/api/activities/activities/unexpired/', api_params)
        return create_success_response(data)
    except Exception as e:
        return create_error_response(e)

# 2. Get Listings
get_listings_tool = {
    "type": "function",
    "function": {
        "name": "get_listings",
        "description": "获取万达双塔的房源列表。可以查询不同楼层、区域的房源信息。",
        "parameters": {
            "type": "object",
            "properties": {
                "search": {
                    "type": "string",
                    "description": "搜索关键词"
                },
                "page": {
                    "type": "integer",
                    "description": "分页页码",
                    "default": 1
                },
                "location__floor": {
                    "type": "integer",
                    "description": "楼层"
                },
                "location__unit": {
                    "type": "string",
                    "description": "单元号"
                },
                "location__zone": {
                    "type": "string",
                    "description": "行政区划/楼栋。仅在用户明确指定特定楼栋时使用。可选值：公寓1栋, 公寓2栋, 公寓5栋, 北塔9栋, 南塔8栋"
                },
                "ordering": {
                    "type": "string",
                    "description": "排序字段"
                }
            }
        }
    }
}

async def get_listings_handler(args):
    print(f"🏠 调用房源API: {args}")
    try:
        data = await fetch_json('https://wanda.tangledup-ai.com/api/listings/', args)
        return create_success_response(data)
    except Exception as e:
        return create_error_response(e)

# 3. Get Merchants
get_merchants_tool = {
    "type": "function",
    "function": {
        "name": "get_merchants",
        "description": "查询万达双塔的入驻商户信息。",
        "parameters": {
            "type": "object",
            "properties": {
                "search": {
                    "type": "string",
                    "description": "搜索关键词，如商户名称"
                },
                "page": {
                    "type": "integer",
                    "description": "分页页码",
                    "default": 1
                },
                "page_size": {
                    "type": "integer",
                    "description": "每页数量",
                    "default": 10
                },
                "location__zone": {
                    "type": "string",
                    "description": "行政区划/楼栋。仅在用户明确指定特定楼栋时使用。可选值：公寓1栋, 公寓2栋, 公寓5栋, 北塔9栋, 南塔8栋"
                },
                "industry_type": {
                    "type": "integer",
                    "description": "行业类型ID"
                },
                "status": {
                    "type": "string",
                    "description": "营业状态，可选值：正常营业, 暂停营业, 已停业"
                },
                "approval_status": {
                    "type": "string",
                    "description": "审核状态，可选值：pending, approved, rejected"
                },
                "is_featured": {
                    "type": "boolean",
                    "description": "是否精选"
                },
                "ordering": {
                    "type": "string",
                    "description": "排序字段"
                }
            }
        }
    }
}

async def get_merchants_handler(args):
    print(f"🏢 调用商户API: {args}")
    try:
        data = await fetch_json('https://wanda.tangledup-ai.com/api/merchants/', args)
        return create_success_response(data)
    except Exception as e:
        return create_error_response(e)

# 4. Get Registration
get_registration_tool = {
    "type": "function",
    "function": {
        "name": "get_registration",
        "description": "通过手机号查询活动报名信息。",
        "parameters": {
            "type": "object",
            "properties": {
                "phone_number": {
                    "type": "string",
                    "description": "报名时使用的手机号"
                }
            },
            "required": ["phone_number"]
        }
    }
}

async def get_registration_handler(args):
    print(f"📋 调用报名查询API: {args}")
    phone_number = args.get("phone_number")
    if not phone_number:
        return create_error_response('必须提供手机号')

    try:
        url = f"https://wanda.tangledup-ai.com/api/activities/registrations/ongoing/{phone_number}/"
        print(f"🌐 Fetching: {url}")
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers={'accept': 'application/json'}) as response:
                if response.status == 404:
                    return create_error_response('您的报名信息有误')
                
                if response.status != 200:
                    raise Exception(f"API request failed with status {response.status}: {response.reason}")
                
                data = await response.json()
                
                if isinstance(data, list) and len(data) == 0:
                    return create_error_response('您的报名信息有误')
                
                return create_success_response(data)
    except Exception as e:
        return create_error_response(e)

# --- Exports ---

TOOLS = [
    get_activities_tool,
    get_listings_tool,
    get_merchants_tool,
    get_registration_tool
]

HANDLERS = {
    "get_activities": get_activities_handler,
    "get_listings": get_listings_handler,
    "get_merchants": get_merchants_handler,
    "get_registration": get_registration_handler
}

INDUSTRY_TYPES_MAPPING = """
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
"""

def get_tool_summary():
    summary = []
    for tool in TOOLS:
        t_def = tool["function"]
        lines = [f"- {t_def['name']}: {t_def['description']}"]
        if "parameters" in t_def and "properties" in t_def["parameters"]:
            for name, schema in t_def["parameters"]["properties"].items():
                desc = schema.get("description", "")
                lines.append(f"  - {name}: {desc}")
        summary.append("\n".join(lines))
    return "\n\n".join(summary)

WANDA_SYSTEM_PROMPT_SEGMENT = f"""
你现在可以访问万达双塔的实时数据，包括活动、房源和商户信息。

可用工具：
{get_tool_summary()}

{INDUSTRY_TYPES_MAPPING}

# 核心交互规则（最高优先级）

## 1. 商户查询必须先分类（Clarification First）
当用户问“附近有哪些商户”、“推荐个店”、“有哪些商家”等**宽泛**问题时：
- **必须**先回复询问用户感兴趣的业态：“万达双塔汇聚了餐饮美食、美容美发、法律咨询等多种业态，请问您想了解哪一类呢？”

## 2. 播报式回答（Soft Polishing）
任何工具调用后，**严禁**直接甩出表格或数据列表。请遵循“先口播，后详情”的结构：
- **第一步（口播）**：用自然、亲切、有吸引力的广播语气介绍查询结果。挑选 1-2 个重点结果（如名称、特色、状态）融入到口语介绍中。
  - *示例*：“为您查询到目前有一家特色的**大成律师事务所**，位于5层，正处于正常营业状态...”

## 3. 其他注意事项
- 查询特定行业商户时，必须优先检查行业类型对照表，如果匹配则使用 industry_type 参数。
- 对于其他工具（活动、房源），如果没有筛选条件，可以先获取概览。
- 可以在一次回复中调用多个工具。
"""



