# OpenAI Chat Completions API 兼容

> 来源：<https://mimo.mi.com/docs/zh-CN/api/chat/openai-api>（MiMo 官方文档，抓取于 2026-08-03）
> 小米 MiMo 提供的 **OpenAI Chat Completions 兼容接口**，基于 `POST /v1/chat/completions`。

## 请求地址

```text
https://api.xiaomimimo.com/v1/chat/completions
```

## 请求头

接口支持以下两种认证方式，请选择其中一种添加到请求头中：

**API Key 鉴权**

```bash
api-key: $MIMO_API_KEY
Content-Type: application/json
```

**Bearer 鉴权**

```bash
Authorization: Bearer $MIMO_API_KEY
Content-Type: application/json
```

## 请求体

### 请求体参数

- `messages` — 类型 `array`, **必填**. 对话的消息列表。
  - `Developer message` — 类型 `object`, 可选. 开发者提供的指令，模型应遵循这些指令，而不受用户发送的消息影响。
    - `content` — 类型 `['string', 'array']`, **必填**. 开发者消息的内容。
      - `Text content` — 类型 `string`, 可选. 开发者消息的内容。
      - `Array of content parts` — 类型 `array`, 可选. 一个由指定类型的内容部分组成的数组。对于开发者消息，仅支持 `text` 类型。
        - `Text content part` — 类型 `object`, 可选.
          - `text` — 类型 `string`, **必填**. 文本内容。
          - `type` — 类型 `string`, **必填**. 内容部分的类型。
    - `role` — 类型 `string`, **必填**. 开发者消息的角色。 可选值：`developer`
    - `name` — 类型 `string`, 可选. 参与者的可选名称。为模型提供信息以区分相同角色的参与者。
  - `System message` — 类型 `object`, 可选. 开发者提供的指令，模型应遵循这些指令，而不受用户发送的消息影响。
    - `content` — 类型 `['string', 'array']`, **必填**. 系统消息的内容。
      - `Text content` — 类型 `string`, 可选. 系统消息的内容。
      - `Array of content parts` — 类型 `array`, 可选. 一个由指定类型的内容部分组成的数组。对于系统消息，仅支持 `text` 类型。
        - `Text content part` — 类型 `object`, 可选.
          - `text` — 类型 `string`, **必填**. 文本内容。
          - `type` — 类型 `string`, **必填**. 内容部分的类型。
    - `role` — 类型 `string`, **必填**. 系统消息角色。 可选值：`system`
    - `name` — 类型 `string`, 可选. 参与者的可选名称。为模型提供信息以区分相同角色的参与者。
  - `User message` — 类型 `object`, 可选. 由终端用户发送的消息，包含提示或额外的上下文信息。
    - `content` — 类型 `['string', 'array']`, **必填**. 用户消息的内容。
      - `Text content` — 类型 `string`, 可选. 文本消息内容。
      - `Array of content parts` — 类型 `array`, 可选. 一个由指定类型的内容部分组成的数组。支持的选项因用于生成响应的模型而异。可包含文本、图像、音频或视频输入。  当前仅 `mimo-v2.5` 模型支持图像、音频或视频输入。
        - `Text content part` — 类型 `object`, 可选.
          - `text` — 类型 `string`, **必填**. 文本内容。
          - `type` — 类型 `string`, **必填**. 内容部分的类型。
        - `Image content part` — 类型 `object`, 可选.
          - `image_url` — 类型 `object`, **必填**.
            - `url` — 类型 `string`, **必填**. 图像的 URL 或 Base64 编码的图像数据。
          - `type` — 类型 `string`, **必填**. 内容部分的类型。 可选值：`image_url`
        - `Audio content part` — 类型 `object`, 可选.
          - `input_audio` — 类型 `object`, **必填**.
            - `data` — 类型 `string`, **必填**. 音频的 URL 或 Base64 编码的音频数据。
          - `type` — 类型 `string`, **必填**. 内容部分的类型。 可选值：`input_audio`
        - `Video content part` — 类型 `object`, 可选.
          - `video_url` — 类型 `object`, **必填**.
            - `url` — 类型 `string`, **必填**. 视频的 URL 或 Base64 编码的视频数据。
          - `fps` — 类型 `number`, 可选, 默认值 `2`. 每秒抽帧数。 所需范围：`[0.1, 10.0]`
          - `media_resolution` — 类型 `string`, 可选, 默认值 `default`. 分辨率档次。 可选值：`default`，`max`
          - `type` — 类型 `string`, **必填**. 内容部分的类型。 可选值：`video_url`
    - `role` — 类型 `string`, **必填**. 用户消息的角色。 可选值：`user`
    - `name` — 类型 `string`, 可选. 参与者的可选名称。为模型提供信息以区分相同角色的参与者。
  - `Assistant message` — 类型 `object`, 可选. 模型响应用户消息发送的消息。
    - `role` — 类型 `string`, **必填**. 助手消息的角色。 可选值：`assistant`
    - `content` — 类型 `['string', 'array']`, 可选. 助手消息的内容。除非指定了 `tool_calls`，否则为必需。
      - `Text content` — 类型 `string`, 可选. 助手消息的内容。
      - `Array of content parts` — 类型 `array`, 可选. 一个由指定类型的内容部分组成的数组。可以是一个或多个 `text` 类型。
        - `Text content part` — 类型 `object`, 可选.
          - `text` — 类型 `string`, **必填**. 文本内容。
          - `type` — 类型 `string`, **必填**. 内容部分的类型。
    - `name` — 类型 `string`, 可选. 参与者的可选名称。为模型提供信息以区分相同角色的参与者。
    - `tool_calls` — 类型 `array`, 可选. 模型生成的工具调用，如函数调用。
      - `Function tool call` — 类型 `object`, 可选. 模型创建的对函数工具的调用。
        - `function` — 类型 `object`, **必填**. 模型调用的函数。
          - `arguments` — 类型 `string`, **必填**. 调用函数时所需的参数，由模型以 JSON 格式生成。请注意，模型生成的内容并非总是有效的 JSON，还可能虚构出函数 schema 中未定义的参数。在调用函数前，请在代码中验证这些参数。
          - `name` — 类型 `string`, **必填**. 要调用的函数名称。
        - `id` — 类型 `string`, **必填**. 工具调用的 ID。
        - `type` — 类型 `string`, **必填**. 工具类型。目前仅支持 `function`。
  - `Tool message` — 类型 `object`, 可选.
    - `content` — 类型 `['string', 'array']`, **必填**. 工具消息的内容。
      - `Text content` — 类型 `string`, 可选. 工具消息的内容。
      - `Array of content parts` — 类型 `array`, 可选. 一个由指定类型的内容部分组成的数组。对于工具消息，仅支持 `text` 类型。
        - `Text content part` — 类型 `object`, 可选.
          - `text` — 类型 `string`, **必填**. 文本内容。
          - `type` — 类型 `string`, **必填**. 内容部分的类型。
    - `role` — 类型 `string`, **必填**. 消息作者的角色。 可选值：`tool`
    - `tool_call_id` — 类型 `string`, **必填**. 此消息响应的工具调用。
- `model` — 类型 `string`, **必填**. 用于生成响应的模型 ID。 可选值：`mimo-v2.5-pro`，`mimo-v2.5`
- `frequency_penalty` — 类型 `['number', 'null']`, 可选, 默认值 `0`. 取值范围在 -2.0 到 2.0 之间的数值。如果该值为正，那么新 token 会根据其在已有文本中的出现频率受到相应的惩罚，降低模型重复相同内容的可能性。 所需范围：`[-2.0, 2.0]`
- `max_completion_tokens` — 类型 `['integer', 'null']`, 可选. 对话补全中可以生成的 token 数的上限，包括可见的输出 token 数和推理 token 数。
  - `mimo-v2.5-pro` 的默认值 `131072`
  - `mimo-v2.5` 的默认值为 `32768`
  所需范围：`[1, 131072]`
- `presence_penalty` — 类型 `['number', 'null']`, 可选, 默认值 `0`. 取值范围在 -2.0 到 2.0 之间的数值。如果该值为正，那么新 token 会根据其是否已在已有文本中出现受到相应的惩罚，从而增加模型谈论新主题的可能性。 所需范围：`[-2.0, 2.0]`
- `response_format` — 类型 `object`, 可选. 一个指定模型必须输出的格式的对象。
  - `Text` — 类型 `object`, 可选. 默认响应格式。用于生成文本响应。
    - `type` — 类型 `string`, **必填**. 所定义的响应格式类型。仅为 `text`。
  - `JSON object` — 类型 `object`, 可选. JSON 对象响应格式。请注意，若系统消息或用户消息中未指示模型生成 JSON，模型将不会输出 JSON 格式内容。
    - `type` — 类型 `string`, **必填**. 所定义的响应格式类型。仅为 `json_object`。
- `stop` — 类型 `['string', 'array', 'null']`, 可选, 默认值 `null`. 最多 4 个序列，当 API 生成到这些序列时会停止继续生成 token。返回的文本中不会包含这些停止序列。
- `stream` — 类型 `['boolean', 'null']`, 可选, 默认值 `false`. 如果设置为 `true`，模型的响应数据会在生成过程中通过SSE（server-sent events）的形式流式传输到客户端。
- `thinking` — 类型 `object`, 可选. 这个参数用于控制模型是否启用思维链。  注意：在思考模式下的多轮工具调用过程中，模型会在返回 `tool_calls` 字段的同时返回 `reasoning_content` 字段。若要继续对话，建议在后续每次请求的 `messages` 数组中保留所有历史 `reasoning_content`，以获得最佳表现。  在思考模式下，`mimo-v2.5-pro`、`mimo-v2.5` 模型不支持自定义 `temperature` 和 `top_p` 参数。即使传入该参数，实际生效值也会被模型强制采用其推荐默认值 `1.0` 和 `0.95`。
  - `type` — 类型 `string`, **必填**. 是否启用思维链
    - `mimo-v2.5-pro`，`mimo-v2.5` 默认值为 `enabled`
    可选值：`enabled`，`disabled`
- `temperature` — 类型 `number`, 可选. 要使用的采样温度，介于 0 和 1.5 之间。较高的值（如 0.8）会使输出更加随机，而较低的值（如 0.2）会使其更加集中和确定性。我们通常建议更改此值或 `top_p`，但不要同时更改。  在思考模式下，`mimo-v2.5-pro`、`mimo-v2.5` 模型不支持自定义 `temperature` 参数。即使传入该参数，实际生效值也会被模型强制采用其推荐默认值 `1.0`。
  - `mimo-v2.5-pro`，`mimo-v2.5` 默认值为 `1.0`
  所需范围：`[0, 1.5]`
- `tool_choice` — 类型 `string`, 可选. 控制模型如何选择工具。  注意：当 `tool_choice` 传入非 `auto` 值时，后端会默认移除该字段，模型响应行为仍等同于 `auto` 模式（该逻辑保留调整的可能性）。 可选值：`auto`
- `tools` — 类型 `array`, 可选. 模型可能调用的工具列表。目前仅支持函数作为工具。  注意：在思考模式下的多轮工具调用过程中，模型会在返回 `tool_calls` 字段的同时返回 `reasoning_content` 字段。若要继续对话，建议在后续每次请求的 `messages` 数组中保留所有历史 `reasoning_content`，以获得最佳表现。
  - `Function tool` — 类型 `object`, 可选. 可用于生成响应的函数工具。
    - `function` — 类型 `object`, **必填**.
      - `name` — 类型 `string`, **必填**. 工具函数的名称。必须由 `a-z`、`A-Z`、`0-9` 组成，或包含下划线（`_`）和连字符（`-`），最大长度为64。 所需字符串长度：`1 - 64`
      - `description` — 类型 `string`, 可选. 函数功能的描述，供模型判断何时以及如何调用该函数。
      - `parameters` — 类型 `object`, 可选. 函数接受的参数，以 JSON 模式对象的形式描述。 若省略 `parameters`，则表示该函数的参数列表为空。
      - `strict` — 类型 `boolean`, 可选, 默认值 `false`. 生成函数调用时是否启用严格的模式遵循。若设为 true，模型将严格遵循 `parameters` 字段中定义的确切模式。当 `strict` 为 `true` 时，仅支持 JSON 模式的一个子集。
    - `type` — 类型 `string`, **必填**. 工具类型。目前仅支持 `function`。
  - `Web search tool` — 类型 `object`, 可选. 可用于生成响应的联网搜索工具。详情请参考 [联网搜索](https://mimo.mi.com/#/docs/usage-guide/tool-calling/web-search)。  注意：使用前需要开通 [联网服务插件](https://platform.xiaomimimo.com/#/console/plugin)。
    - `user_location` — 类型 `object`, 可选. 用户地理位置，用于优化模型输出结果
      - `type` — 类型 `string`, **必填**. approximate
      - `country` — 类型 `string`, 可选. 国家
      - `region` — 类型 `string`, 可选. 省份
      - `city` — 类型 `string`, 可选. 城市
      - `district` — 类型 `string`, 可选. 区县
      - `longitude` — 类型 `long`, 可选. 经度
      - `latitude` — 类型 `long`, 可选. 维度
    - `type` — 类型 `string`, **必填**. 工具类型。目前仅支持 `web_search`。
    - `force_search` — 类型 `string`, 可选, 默认值 `false`. 是否启用强制搜索。`true` 强制搜索，`false` 由模型判断是否需要搜索。
    - `max_keyword` — 类型 `integer`, 可选, 默认值 `5`. 限制单轮搜索中可使用的最大关键词数量。 所需范围：`[1, 50]`
    - `limit` — 类型 `integer`, 可选, 默认值 `5`. 限制单次搜索操作返回的最大结果条数。 所需范围：`[1, 50]`
- `top_p` — 类型 `number`, 可选, 默认值 `0.95`. 核采样的概率阈值，用于控制模型生成文本的多样性。`top_p` 值越高，生成的文本多样性越强；`top_p` 值越低，生成的文本确定性越高。 由于 `temperature` 和 `top_p` 均用于控制生成文本的多样性，建议仅设置其中一个参数。  在思考模式下，`mimo-v2.5-pro`、`mimo-v2.5` 模型不支持自定义 `top_p` 参数。即使传入该参数，实际生效值也会被模型强制采用其推荐默认值 `0.95`。 所需范围：`[0.01, 1.0]`

### 请求示例

```bash
curl --location --request POST 'https://api.xiaomimimo.com/v1/chat/completions' \
--header "api-key: $MIMO_API_KEY" \
--header "Content-Type: application/json" \
--data-raw '{
    "model": "mimo-v2.5-pro",
    "messages": [
        {
            "role": "system",
            "content": "You are MiMo, an AI assistant developed by Xiaomi. Today is date: Tuesday, December 16, 2025. Your knowledge cutoff date is December 2024."
        },
        {
            "role": "user",
            "content": "please introduce yourself"
        }
    ],
    "max_completion_tokens": 1024,
    "temperature": 1.0,
    "top_p": 0.95,
    "stream": false,
    "stop": null,
    "frequency_penalty": 0,
    "presence_penalty": 0,
    "thinking": {
        "type": "disabled"
    }
}'
```

## Chat 响应对象（非流式输出）

### 响应示例

```json
{
    "id": "8b51f9e0515949cb8207fbd35ea6ea5c",
    "choices": [
        {
            "finish_reason": "stop",
            "index": 0,
            "message": {
                "content": "Hello! I'm MiMo, Xiaomi's AI assistant created by the Xiaomi LLM-Core team. I'm here to chat, help answer questions, and assist with various tasks—whether it's providing information, brainstorming ideas, or just having a friendly conversation. Feel free to ask me anything, and I'll do my best to help! 😊",
                "role": "assistant",
                "tool_calls": null
            }
        }
    ],
    "created": 1776848906,
    "model": "mimo-v2.5-pro",
    "object": "chat.completion",
    "usage": {
        "completion_tokens": 72,
        "prompt_tokens": 57,
        "total_tokens": 129,
        "completion_tokens_details": {
            "reasoning_tokens": 0
        },
        "prompt_tokens_details": null
    }
}
```

### 响应对象参数

- `choices` — 类型 `array`, 可选. 包含生成的回复选项列表。
  - `finish_reason` — 类型 `string`, 可选. 模型停止生成 token 的原因。如果模型到达自然停止点或提供的停止序列，则为 `stop`；如果达到请求中指定的最大 token 数，则为 `length`；如果模型调用了工具，则为 `tool_calls`。如果内容因触发过滤策略而被拦截，则为 `content_filter`；如果模型检测到了复读，则为 `repetition_truncation`。
  - `index` — 类型 `integer`, 可选. 选项列表中对应选项的索引。
  - `message` — 类型 `object`, 可选. 模型生成的对话补全消息。
    - `content` — 类型 `string`, 可选. 消息的内容。
    - `reasoning_content` — 类型 `string`, 可选. 助手消息中最终答案之前的推理内容。
    - `role` — 类型 `string`, 可选. 消息作者的角色。
    - `tool_calls` — 类型 `array`, 可选. 函数调用启动后，模型会返回待调用的工具以及该调用所需的参数。此参数可包含一个或多个工具响应对象。
      - `Function tool call` — 类型 `object`, 可选. 模型创建的对函数工具的调用。
        - `function` — 类型 `object`, 可选. 模型所调用的函数。
          - `arguments` — 类型 `string`, 可选. 模型生成的用于调用函数的参数，格式为 JSON。请注意，模型生成的内容并非并非总能保证是有效的 JSON，且可能会虚构出函数模式中未定义的参数。在调用函数之前，请在代码中对这些参数进行验证。
          - `name` — 类型 `string`, 可选. 要调用的函数的名称。
        - `id` — 类型 `string`, 可选. 工具调用的 ID。
        - `type` — 类型 `string`, 可选. 工具的类型。目前仅支持 `function`。
    - `annotations` — 类型 `array`, 可选. 联网搜索后，模型会返回全部引用网址的注释。
      - `web_search tool call` — 类型 `object`, 可选. 模型创建的对联网搜索的调用。
        - `logo_url` — 类型 `string`, 可选. logo网址。
        - `publish_time` — 类型 `string`, 可选. 发布时间。
        - `site_name` — 类型 `string`, 可选. 网站名称。
        - `summary` — 类型 `string`, 可选. 总结。
        - `title` — 类型 `string`, 可选. 标题。
        - `type` — 类型 `string`, 可选. 类型。
        - `url` — 类型 `string`, 可选. 网址。
    - `error_message` — 类型 `string`, 可选. 联网搜索的错误信息。
- `created` — 类型 `integer`, 可选. 对话补全对象创建时的 Unix 时间戳（以秒为单位）。
- `id` — 类型 `string`, 可选. 响应的唯一标识符。
- `model` — 类型 `string`, 可选. 用于生成结果的模型。
- `object` — 类型 `string`, 可选. 对象类型，仅为 `chat.completion`。
- `usage` — 类型 `['object', 'null']`, 可选. 该对话补全请求的用量信息。
  - `completion_tokens` — 类型 `integer`, 可选. 模型输出内容花费的 token。
  - `prompt_tokens` — 类型 `integer`, 可选. 提示词使用的 token 数量。
  - `total_tokens` — 类型 `integer`, 可选. 请求中使用的 token 总数（提示词 + 补全结果）。
  - `completion_tokens_details` — 类型 `object`, 可选. 补全中使用的 token 数量明细。
    - `reasoning_tokens` — 类型 `integer`, 可选. 模型为推理生成的 token 数量。
  - `prompt_tokens_details` — 类型 `object`, 可选. 提示中使用的 token 数量明细。
    - `cached_tokens` — 类型 `integer`, 可选. 命中缓存的 token 数量。
    - `audio_tokens` — 类型 `integer`, 可选. 提示中存在的音频输入 token 数量。
    - `image_tokens` — 类型 `integer`, 可选. 提示中存在的图像输入 token 数量。
    - `video_tokens` — 类型 `integer`, 可选. 提示中存在的视频输入 token 数量。
  - `web_search_usage` — 类型 `object`, 可选. 联网搜索 api 的调用量明细。
    - `tool_usage` — 类型 `integer`, 可选. 联网搜索 api 的调用次数。
    - `page_usage` — 类型 `integer`, 可选. 联网搜索 api 返回的网页数。

## Chat 响应 chunk 对象（流式输出）

### 响应对象参数

- `choices` — 类型 `array`, 可选. 包含生成的回复选项列表。
  - `delta` — 类型 `object`, 可选. 流式模型响应生成的对话补全增量。
    - `content` — 类型 `string`, 可选. 数据块消息的内容。
    - `reasoning_content` — 类型 `string`, 可选. 助手消息中最终答案之前的推理内容。
    - `role` — 类型 `string`, 可选. 消息作者的角色。
    - `tool_calls` — 类型 `array`, 可选. 函数调用启动后，模型会返回待调用的工具以及该调用所需的参数。此参数可包含一个或多个工具响应对象。
      - `index` — 类型 `integer`, 可选. 在 `tool_calls` 列表中被调用工具的索引，从 0 开始。
      - `function` — 类型 `object`, 可选. 调用的函数。
        - `arguments` — 类型 `string`, 可选. 模型生成的用于调用函数的参数，格式为 JSON。请注意，模型生成的内容并非并非总能保证是有效的 JSON，且可能会虚构出函数模式中未定义的参数。在调用函数之前，请在代码中对这些参数进行验证。
        - `name` — 类型 `string`, 可选. 要调用的函数的名称。
      - `id` — 类型 `string`, 可选. 工具调用的 ID。
      - `type` — 类型 `string`, 可选. 工具的类型。目前仅支持 `function`。
    - `annotations` — 类型 `array`, 可选. 联网搜索后，模型会返回全部引用网址的注释。
      - `web_search tool call` — 类型 `object`, 可选. 模型创建的对联网搜索的调用。
        - `logo_url` — 类型 `string`, 可选. logo网址。
        - `publish_time` — 类型 `string`, 可选. 发布时间。
        - `site_name` — 类型 `string`, 可选. 网站名称。
        - `summary` — 类型 `string`, 可选. 总结。
        - `title` — 类型 `string`, 可选. 标题。
        - `type` — 类型 `string`, 可选. 类型。
        - `url` — 类型 `string`, 可选. 网址。
    - `error_message` — 类型 `string`, 可选. 联网搜索链路的错误信息。
  - `finish_reason` — 类型 `['string', 'null']`, 可选. 模型停止生成 token 的原因。如果模型到达自然停止点或提供的停止序列，则为 `stop`；如果达到请求中指定的最大 token 数，则为 `length`；如果模型调用了工具，则为 `tool_calls`。如果内容因触发过滤策略而被拦截，则为 `content_filter`；如果模型检测到了复读，则为 `repetition_truncation`。
  - `index` — 类型 `integer`, 可选. 选项列表中对应选项的索引。
- `created` — 类型 `integer`, 可选. 对话补全对象创建时的 Unix 时间戳（以秒为单位）。每个数据块均使用相同的时间戳。
- `id` — 类型 `string`, 可选. 对话补全对象的唯一标识符。每个数据块均使用相同的 ID。
- `model` — 类型 `string`, 可选. 用于生成结果的模型。
- `object` — 类型 `string`, 可选. 对象类型，仅为 `chat.completion.chunk`。
- `usage` — 类型 `['object', 'null']`, 可选. 该对话补全请求的用量信息。
  - `completion_tokens` — 类型 `integer`, 可选. 模型输出内容花费的 token。
  - `prompt_tokens` — 类型 `integer`, 可选. 提示词使用的 token 数量。
  - `total_tokens` — 类型 `integer`, 可选. 请求中使用的 token 总数（提示词 + 补全结果）。
  - `completion_tokens_details` — 类型 `object`, 可选. 补全中使用的 token 数量明细。
    - `reasoning_tokens` — 类型 `integer`, 可选. 模型为推理生成的 token 数量。
  - `prompt_tokens_details` — 类型 `object`, 可选. 提示中使用的 token 数量明细。
    - `cached_tokens` — 类型 `integer`, 可选. 命中缓存的 token 数量。
    - `audio_tokens` — 类型 `integer`, 可选. 提示中存在的音频输入 token 数量。
    - `image_tokens` — 类型 `integer`, 可选. 提示中存在的图像输入 token 数量。
    - `video_tokens` — 类型 `integer`, 可选. 提示中存在的视频输入 token 数量。
  - `web_search_usage` — 类型 `object`, 可选. 联网搜索 api 的调用量明细。
    - `tool_usage` — 类型 `integer`, 可选. 联网搜索 api 的调用次数。
    - `page_usage` — 类型 `integer`, 可选. 联网搜索 api 返回的网页数。
