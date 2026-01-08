- - # 自动化测试平台 (ATP) 前端界面设计说明书
  
    | 版本号 | 日期       | 修改人 | 备注 |
    | :----- | :--------- | :----- | :--- |
    | v0.1.0 | 2026-01-05 | ycb    | 初稿 |
  
    ---
  
    ## 1. 全局设计规范 (Global Style)
  
    *   **布局模式**: 经典的 Admin Layout。
        *   **左侧**: 侧边栏导航 (Sidebar)，支持折叠。
        *   **顶部**: 顶栏 (Header)，包含面包屑导航、项目切换器 (Project Switcher)、用户头像/退出菜单。
        *   **中间**: 内容区域 (Content)，统一白色卡片式背景，内边距 (Padding) 20px。
    *   **交互原则**:
        *   **反馈**: 所有增删改 (Create/Update/Delete) 操作必须有 Message 弹窗提示 (Success/Error)。
        *   **加载**: 表格加载、按钮提交时必须有 Loading 状态，防止重复点击。
        *   **空状态**: 当列表无数据时，展示 Empty 占位图。
  
    ---
  
    ## 2. 站点地图 (Site Map)
  
    ```text
    - 登录/注册页 (Login)
    - 平台主页 (Layout)
      ├── 仪表盘 (Dashboard)
      ├── 项目管理 (Project) - [顶部全局切换当前工作空间]
      ├── 用例管理 (Test Cases)
      │   └── 列表页 (支持 Git 同步)
      ├── 测试计划 (Test Plans)
      │   ├── 创建/编辑计划
      │   └── 执行记录 (Executions) -> 详情页(控制台日志)
      ├── 报告中心 (Reports)
      │   └── 列表页
      │   └── 详情页 (Allure 报告 Iframe 嵌入 + AI 分析)
      └── 配置中心 (Settings)
          ├── 环境配置 (Environments)
          └── 密钥管理 (Secrets)
    ```
  
    ## 3. 核心页面详细设计
  
    ### 3.1 登录页 (Login Page)
  
    - **布局**: 屏幕居中卡片式布局，整体风格简洁大气 (Minimalist Design)。
    - **表单元素**:
      1. **账号**: Input 输入框 (必填，Placeholder: 用户名或邮箱)。
      2. **密码**: Input 输入框 (必填，支持小眼睛显示/隐藏)。
      3. **登录按钮**: Button (Primary)。
      4. **注册入口**: 文字链接 "没有账号？立即注册"。
    - **交互逻辑**:
      - **键盘支持**: 在密码框按 Enter 键触发登录。
      - **校验**:
        - 若为空，Toast 提示“请输入账号/密码”。
        - 账号框禁止输入 < > 等特殊字符。
      - **提交状态**: 点击按钮后，按钮进入 Loading 状态并禁用，直到接口返回。
      - **登录成功**:
        - 将 access_token 和 refresh_token 存入 localStorage。
        - Toast 提示“欢迎回来”。
        - 路由跳转至 redirect 参数指向的页面，无参数则跳 Dashboard
  
    
  
    ### 3.1.1 注册页 (Register Page)
  
    - **表单元素**:
      1. **账号**: Input (必填，建议强制邮箱格式以用于找回密码)。
      2. **密码**: Input (必填)。
      3. **确认密码**: Input (必填，前端校验两次输入是否一致)。
      4. **注册按钮**: Button。
      5. **返回登录**: 文字链接。
    - **交互逻辑**:
      - **密码强度**: 需校验 "最少 6 位，包含数字+字母"。
      - **注册成功**:
        - Toast 提示“注册成功，请登录”。
        - 自动跳转至 **登录页**，并自动回填账号。
      - **注册失败**:
        - 根据后端 Error Code 提示具体原因 (e.g., "该邮箱已被占用")。
  
    
  
    ### 3.2 仪表盘 (Dashboard)
  
    - **目的**: 展示当前选中项目 (Project) 的测试健康度概览。
    - **区域划分**:
      1. **统计卡片 (Statistic Cards)**: 一排 4 个。
         - **用例总数**: 来源于 Git 同步的数量。
         - **近 7 天构建数**: 执行次数。
         - **最新构建通过率**: e.g., 98% (绿色) / 50% (红色)。
         - **平均耗时**: e.g., 3m 20s。
      2. **趋势图 (Charts)**:
         - 使用 ECharts 绘制折线图：“近 30 次构建通过率趋势”。
      3. **快捷入口 (Quick Actions)**:
         - [发起新测试]
         - [同步 Git 用例]
  
    ### 3.3 用例管理 (Test Cases) - *核心差异点*
  
    - **设计理念**: 用例由 Git 托管，Web 端只读，不提供“新建用例”按钮。
    - **顶部工具栏**:
      - **Git 仓库信息**: 显示当前项目绑定的 Git URL (只读文本)。
      - **分支选择**: Select 下拉框 (main/develop...)，默认选中 main。
      - **[同步用例] 按钮**: 点击后触发后端 pytest --collect-only 任务。
        - *交互*: 点击后按钮进入 Loading 状态，上方显示进度条，直到 WebSocket 推送同步完成消息。
    - **用例列表 (Table)**:
      - **列定义**:
        - **ID**: 用例唯一标识。
        - **模块**: 文件夹路径 (e.g., tests/api/login).
        - **用例名称**: 函数名 (e.g., test_login_success).
        - **标记 (Markers)**: Tags 展示 (e.g., smoke, p0).
        - **描述**: Docstring 提取的文本。
        - **最近状态**: Pass/Fail 图标。
  
    ### 3.4 测试计划与执行 (Test Plans & Execution)
  
    #### A. 发起测试弹窗 (Run Test Modal)
  
    - **表单项**:
      1. **选择环境**: Select (Dev / Stage / Prod)。
         - *交互*: 若选择 Prod，弹出红色 Alert 警告：“生产环境将强制开启只读模式！”。
      2. **选择分支**: Select (默认 main)。
      3. **镜像策略**: Radio (使用缓存镜像 / 强制重新构建)。
      4. **用例筛选**:
         - **按 Marker**: Select (e.g., -m smoke)。
         - **按 Keyword**: Input (e.g., -k login_module)。
    - **[立即执行] 按钮**: 发送 POST 请求，跳转至“执行详情页”。
  
    #### B. 执行详情页 (Console View) - *技术难点*
  
    - **布局**: 类似 CI 工具 (Jenkins/GitHub Actions) 的构建详情页。
    - **状态栏**: 顶部展示 Status: Running (动态刷新) | Duration: 00:02:15。
    - **日志终端 (Terminal)**:
      - 样式: 黑色背景，绿色字体 (Monospace 字体)，模拟 Linux 终端。
      - **逻辑**: 通过 WebSocket 连接或每 2 秒轮询 Redis 接口。
      - **内容**: 实时追加显示 Celery Worker 回传的 StdOut 日志。
      - *自动滚动*: 当有新日志时，滚动条自动到底部。
  
    ### 3.5 报告中心 (Report Center)
  
    - **列表页**:
      - 表格展示历史执行记录：ReportID, 触发时间, 耗时, 通过率, 触发人。
      - 状态列：Pending (灰) -> Running (蓝) -> Success (绿) / Fail (红) / Error (橙)。
      - 操作列：[查看详情]
    - **详情页**:
      - **概览头**: 简报 (Total: 52, Pass: 50, Fail: 2, Error: 0)。
      - **AI 分析按钮 (v0.1.1)**: [🤖 AI 分析失败原因]。
        - *交互*: 点击后按钮 Loading，后端请求 LLM，成功后弹出 Dialog 展示 Markdown 格式的修复建议。
      - **Allure 嵌入区**:
        - 使用 <iframe src="..."> 标签。
        - src 指向后端静态文件托管服务的 index.html 地址。
        - 高度自适应屏幕剩余空间。
  
    ### 3.6 配置中心 (Settings)
  
    - **环境管理 (Environments)**:
      - Tabs: Dev / Stage / Prod。
      - Form: Base URL, Database Host, Redis Host。
    - **密钥管理 (Secrets)**:
      - Table: Key, Value (默认显示 ******, 点击小眼睛输入密码后显示明文), Description。
      - 用途: 存储 API Token, 数据库密码等敏感信息，用于注入 Docker 容器环境变量。
  
    
  
    ## 4. 给开发者的建议 (Implementation Tips)
  
    ### 4.1 技术选型建议
  
    - **框架**: Vue 3 (使用 <script setup> 语法糖) + Vite (构建工具)。
    - **UI 组件库**: **Element Plus** (组件丰富，文档完善，适合中后台)。
    - **路由**: Vue Router 4.x。
    - **状态管理**: **Pinia** (替代 Vuex，用于存储 User Token, 当前选中的 project_id)。
    - **网络请求**: **Axios**。
      - *拦截器配置*: 请求头自动携带 Authorization: Bearer {token}；响应拦截器处理 401 状态码自动跳转登录页。
    - **图表库**: **ECharts** (用于仪表盘)。
  
    ### 4.2 开发优先级 (Roadmap)
  
    1. **Day 1**: 初始化 Vite 项目，配置 Element Plus，搭建 Layout (Sidebar + Header)。
    2. **Day 2**: 封装 Axios，完成 Login 页面与 Authentication 流程。
    3. **Day 3**: 完成“执行详情页”的日志轮询/WebSocket 逻辑 (可先用 Mock 数据)。
    4. **Day 4**: 嵌入 Allure Iframe，处理跨域或加载问题。
    5. **Day 5**: 完成用例列表和配置中心的 CRUD。
  
    ### 4.3 Mock 数据示例
  
    在后端接口未就绪前，前端可使用以下 Mock 数据先行开发“执行详情页”：
  
    
  
    **GET /api/v1/executions/1024/logs**
  
    ```JSON
    {
      "code": 200,
      "data": {
        "status": "running",
        "logs": "[2026-01-05 10:00:01] pytest starting...\n[2026-01-05 10:00:02] collected 5 items\n[2026-01-05 10:00:03] tests/api/test_login.py . [20%]\n"
      }
    }
    ```
