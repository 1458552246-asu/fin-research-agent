"""Mock data for demo mode - pre-built responses for common queries."""

import sys
from pathlib import Path
from typing import Dict, List

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.bull_bear_analyzer import BullBearAnalysis, Viewpoint


# =============================================================================
# Mock Search Results for Demo Queries
# =============================================================================

MOCK_SEARCH_RESULTS = {
    # =========================================================================
    # 01. NVIDIA - 业绩会关键指引
    # =========================================================================
    "nvidia": [
        {
            "file_id": 1001,
            "title": "NVIDIA FY2028 Q1业绩说明会纪要",
            "source_type": "AlphaEngine",
            "date": "2026-06-25",
            "author": "NVIDIA IR",
            "url": "https://investor.nvidia.com/events",
            "content": """【NVIDIA FY2027 Q1业绩说明会完整纪要】

一、核心财务数据：
- 数据中心收入达到263亿美元，同比增长73%，环比增长12%
- 总收入突破300亿美元大关，创历史新高
- 毛利率维持在75.2%的高位，显示定价能力依然强劲
- 运营利润率达到62%，同比提升5个百分点

二、Blackwell架构更新：
- Blackwell GPU全面量产，良率已提升至85%以上
- 供不应求状态持续，订单可见度已排至2027年Q1
- 下季度收入指引280亿美元，超华尔街一致预期15%

三、客户结构变化：
- 企业客户占比提升至45%，较去年同期增长10个百分点
- 主权AI需求来自30+国家，成为新增长引擎
- 云厂商资本开支持续加码，微软、谷歌、亚马逊均上调AI投入

四、管理层展望：
- CEO黄仁勋强调AI推理需求正在加速，将成为下一个增长曲线
- 预计FY2027全年收入将超过1200亿美元
- Rubin架构（下一代）研发进展顺利，预计2027年下半年推出""",
            "snippet": "数据中心收入263亿美元同比+73%，下季指引280亿超预期"
        },
        {
            "file_id": 1002,
            "title": "NVIDIA供应链专家访谈 - Blackwell产能深度解析",
            "source_type": "专家访谈",
            "date": "2026-06-22",
            "author": "半导体供应链专家",
            "content": """【专家访谈纪要 - NVIDIA Blackwell产能与供应链】

受访专家：某头部封测厂高管，从业15年

一、Blackwell良率情况：
- 目前Blackwell GPU良率已稳定在85%左右，较初期提升显著
- 主要改进来自台积电3nm工艺的持续优化
- B200良率略低于B100，但差距在缩小

二、产能瓶颈分析：
- 台积电CoWoS先进封装仍是最大瓶颈，产能利用率超过100%
- 预计2026年Q3产能将提升30%，但仍无法完全满足需求
- ABF载板供应趋于平衡，不再是主要限制因素

三、订单与交付情况：
- 云厂商订单可见度已排到2027年Q1，锁定产能
- 企业客户交付周期约16-20周，较去年缩短
- 中国区受限后，产能重新分配给其他区域客户

四、专家判断：
- 供需紧张将持续到2026年上半年结束
- 2026年下半年有望达到供需平衡
- 长期看，台积电扩产速度将决定NVIDIA增长上限""",
            "snippet": "Blackwell良率85%，CoWoS是瓶颈，供需紧张持续到2026H1"
        },
        {
            "file_id": 1003,
            "title": "@jensen_huang关于AI基础设施的推文",
            "source_type": "Twitter推文",
            "date": "2026-06-26",
            "author": "jensen_huang",
            "url": "https://twitter.com/jensen_huang",
            "content": """【黄仁勋Twitter原文及解读】

原文：
"The next industrial revolution is here. Every company is becoming an AI company. Blackwell is the engine. Sovereign AI demand from 30+ countries. The age of AI inference is upon us. $NVDA"

要点解读：
1. 强调AI是新一轮工业革命，不是短期炒作
2. "每家公司都在成为AI公司" - 暗示企业AI渗透率将持续提升
3. 主权AI需求来自30+国家 - 政府采购成为新增量
4. AI推理时代来临 - 推理需求将超过训练需求
5. Blackwell是核心引擎 - 产品定位清晰

市场反应：推文发布后NVDA盘后涨2.3%""",
            "snippet": "每家公司都在成为AI公司，Blackwell是引擎，30+国家主权AI需求"
        },
        {
            "file_id": 1004,
            "title": "GPU定价与竞争格局深度分析报告",
            "source_type": "AceCampTech",
            "date": "2026-06-20",
            "author": "半导体研究团队",
            "content": """【GPU市场竞争格局深度报告】

一、市场份额分析：
- NVIDIA在AI训练GPU市场份额超过90%，垄断地位稳固
- AI推理市场份额约75%，面临更多竞争
- AMD MI300X在推理市场取得突破，份额约8%
- 云厂商自研芯片（Google TPU、Amazon Trainium）占约10%

二、定价策略：
- Blackwell B200定价较H100提升20-30%
- 客户接受度高，主要因为性价比提升（性能提升4倍）
- 企业版定价略高于云厂商批量采购价
- 维护和软件服务收入占比提升至15%

三、竞争态势：
- AMD MI300X性价比突出，但CUDA生态壁垒难以逾越
- Intel Gaudi系列市场存在感弱，份额不足2%
- 中国市场受限后，国产GPU加速追赶但差距仍大

四、风险因素：
- 云厂商自研芯片进度加速，长期威胁存在
- 中国市场受限影响约5-8%收入
- 估值处于历史高位，对业绩容错率低

五、投资建议：
- 短期看多，业绩超预期概率高
- 中期关注云厂商自研进展
- 长期需警惕技术迭代和竞争加剧""",
            "snippet": "AI训练GPU份额超90%，Blackwell定价提升20-30%客户接受度高"
        }
    ],

    # =========================================================================
    # 02. 另类资管对比 - KKR/Apollo/Blackstone
    # =========================================================================
    "kkr": [
        {
            "file_id": 2001,
            "title": "KKR 2026 Q1业绩说明会纪要",
            "source_type": "AlphaEngine",
            "date": "2026-06-02",
            "author": "KKR IR",
            "url": "https://ir.kkr.com",
            "content": """【KKR 2026年Q1业绩说明会完整纪要】

一、核心业绩指标：
- Fee-Related Earnings (FRE) 达到12.3亿美元，同比增长18%
- AUM突破6010亿美元，创历史新高
- Distributable Earnings达到15.2亿美元，同比+22%
- 管理层上调全年FRE指引至50亿美元（此前48亿）

二、业务板块表现：
- 私募股权：募资环境改善，新基金超额认购
- 基础设施：全球能源转型带动，收入+35%
- 信贷业务：私人信贷持续强劲，AUM+28%
- 房地产：承压但已见底，开始选择性投资

三、战略重点：
- 加大亚太市场投入，日本和韩国为重点
- 扩展wealth management渠道
- 推进数字化转型，提升运营效率

四、管理层展望：
- 2026年下半年并购活动预计回暖
- IPO窗口逐步打开，退出环境改善
- 长期看好私人信贷和基础设施赛道""",
            "snippet": "FRE 12.3亿美元同比+18%，AUM突破6010亿，上调全年FRE指引"
        },
        {
            "file_id": 2002,
            "title": "Apollo 2026 Q1业绩说明会纪要",
            "source_type": "AlphaEngine",
            "date": "2026-06-01",
            "author": "Apollo IR",
            "url": "https://ir.apollo.com",
            "content": """【Apollo 2026年Q1业绩说明会完整纪要】

一、核心业绩指标：
- FRE达到5.2亿美元，同比增长12%
- 总AUM达到6710亿美元，其中信贷占比超过60%
- Athene退休服务贡献显著，保费收入创新高

二、业务亮点：
- 信贷业务持续领跑，私人信贷AUM+32%
- 与Athene协同效应增强，保险+资管双轮驱动
- 中间市场贷款需求旺盛

三、战略转型：
- 从传统PE向多元化资产管理转型成效显著
- 信贷占比持续提升，降低业绩波动性
- 加强与银行合作，扩大资金来源

四、风险提示：
- 利率高位对部分portfolio公司造成压力
- 信贷违约率有抬头迹象，但仍在可控范围""",
            "snippet": "FRE 5.2亿美元同比+12%，AUM 6710亿，向多元化资管转型"
        },
        {
            "file_id": 2003,
            "title": "Blackstone 2026 Q1业绩说明会纪要",
            "source_type": "AlphaEngine",
            "date": "2026-05-30",
            "author": "Blackstone IR",
            "url": "https://ir.blackstone.com",
            "content": """【Blackstone 2026年Q1业绩说明会完整纪要】

一、核心业绩指标：
- FRE达到13.5亿美元，同比增长15%
- AUM突破1.1万亿美元，全球最大另类资管
- Distributable Earnings达到18亿美元

二、业务板块：
- 房地产：承压但开始企稳，物流和数据中心表现亮眼
- 私募股权：退出环境改善，DPI有所回升
- 信贷：私人信贷持续增长，yield稳定
- 基础设施：能源和数字基建需求强劲

三、市场判断：
- 房地产已见底，2026H2开始复苏
- 私人信贷长期增长空间大，银行监管趋严是催化剂
- AI相关投资成为新重点

四、战略举措：
- 加大retail渠道布局
- 扩展亚洲和中东市场
- 增加对AI/数据中心的投资敞口""",
            "snippet": "FRE 13.5亿美元同比+15%，AUM破1.1万亿，全球最大另类资管"
        },
        {
            "file_id": 2004,
            "title": "另类资管行业专家深度访谈",
            "source_type": "专家访谈",
            "date": "2026-06-10",
            "author": "资管行业专家",
            "content": """【专家访谈 - 另类资管行业深度解析】

受访专家：前头部另类资管机构MD，20年从业经验

一、三大机构对比：
- KKR：增速最快但规模最小，执行力强，亚洲布局领先
- Apollo：信贷业务最强，与保险协同独特，收入稳定性最好
- Blackstone：规模最大，品牌溢价明显，房地产专业度高

二、行业趋势判断：
- 私人信贷是未来5年最大增量，银行去杠杆是主因
- 基础设施投资受益于能源转型和数字化
- PE退出仍然困难，但估值已开始松动

三、2026年展望：
- 下半年并购活动将明显回暖
- IPO窗口逐步打开，但选择性强
- 利率下行将提振估值和退出

四、投资建议：
- KKR：高增长，适合进取型投资者
- Apollo：稳健增长，股息吸引力强
- Blackstone：行业龙头，适合长期配置""",
            "snippet": "KKR增速最快、Apollo信贷最强、Blackstone规模领先，下半年并购回暖"
        }
    ],

    # =========================================================================
    # 03. Dell - AI服务器订单与ISG毛利率
    # =========================================================================
    "dell": [
        {
            "file_id": 3001,
            "title": "Dell Technologies FY26 Q1业绩说明会纪要",
            "source_type": "AlphaEngine",
            "date": "2026-06-27",
            "author": "Dell IR",
            "url": "https://investors.delltechnologies.com",
            "content": """ISG收入同比增长42%达到128亿美元，AI服务器收入占比提升至35%。
AI服务器订单backlog达到42亿美元，环比增长25%。但ISG毛利率下滑至18.5%，
低于去年同期的21.2%，主要因为AI服务器毛利率较低。""",
            "snippet": "ISG收入+42%达128亿，AI服务器backlog 42亿，但毛利率降至18.5%"
        },
        {
            "file_id": 3002,
            "title": "服务器产业链专家访谈 - AI Server供应链动态",
            "source_type": "专家访谈",
            "date": "2026-06-25",
            "author": "服务器行业专家",
            "content": """Dell在AI服务器市场份额提升明显，主要受益于与NVIDIA的深度合作。
但需要关注的风险：1）GPU供应仍然紧张，交付周期长；2）AI服务器毛利率低于传统服务器；
3）竞争加剧，HPE和联想都在抢市场。专家判断Dell短期受益但中长期竞争压力大。""",
            "snippet": "Dell AI服务器份额提升，但毛利率承压，中长期竞争压力大"
        },
        {
            "file_id": 3003,
            "title": "PC市场2026展望 - AI PC驱动换机",
            "source_type": "AceCampTech",
            "date": "2026-06-15",
            "author": "TMT研究团队",
            "content": """AI PC渗透率开始提升，企业换机周期有望启动。Dell作为企业PC主要供应商，
CSG业务有望在2026下半年见底回升。但AI PC实际需求仍待观察，溢价能力有限。""",
            "snippet": "AI PC驱动企业换机周期，Dell CSG有望下半年见底"
        },
        {
            "file_id": 3004,
            "title": "@MichaelDell关于AI战略的推文",
            "source_type": "Twitter推文",
            "date": "2026-06-27",
            "author": "MichaelDell",
            "url": "https://twitter.com/MichaelDell",
            "content": """Just announced: Dell AI Factory now powers 85% of Fortune 100 companies'
AI infrastructure. The enterprise AI revolution is just beginning. $DELL""",
            "snippet": "Dell AI Factory覆盖85%财富100强企业AI基础设施"
        }
    ],

    # =========================================================================
    # 04. HBM - 产能扩张与竞争格局
    # =========================================================================
    "hbm": [
        {
            "file_id": 1201,
            "title": "SK海力士 2026 Q1 业绩会纪要",
            "source_type": "AlphaEngine",
            "date": "2026-04-25",
            "author": "SK Hynix IR",
            "url": "https://www.skhynix.com/ir",
            "content": """【SK海力士 2026年Q1业绩说明会纪要】

一、HBM业务核心数据：
- HBM收入同比增长320%，占DRAM收入比重达到35%
- HBM3E出货量环比增长45%，ASP保持稳定
- 与NVIDIA签订2027年供应协议，锁定产能

二、产能扩张计划：
- 2026年HBM产能计划扩产80%，主要投向HBM3E
- 清州M15X工厂已投产，专注HBM生产
- 设备交付周期18个月，2026年产能其实在2024年就要下单

三、技术进展：
- HBM3E 12-Hi产品已量产，良率达到88%
- HBM4样品已送样NVIDIA认证，预计2027年Q2量产
- Hybrid Bonding技术研发进展顺利

四、竞争格局：
- 全球HBM市场份额约53%，保持领先
- 三星追赶迅速，但良率差距仍有8-10个百分点
- 美光进展较慢，份额约15%""",
            "snippet": "HBM收入同比+320%，占DRAM收入35%，2026年扩产80%"
        },
        {
            "file_id": 2201,
            "title": "HBM产业链专家访谈",
            "source_type": "专家访谈",
            "date": "2026-05-15",
            "author": "某半导体设备公司亚太区总监",
            "content": """专家背景：某半导体设备公司亚太区总监

Q: HBM产能扩张的实际进度?
A: SK海力士和三星都在疯狂扩产，但设备交付周期长达18个月。2026年的产能其实在2024年就要下单。

Q: 良率情况如何?
A: HBM3E的良率普遍在80-85%，比HBM3的90%要低。这是因为堆叠层数增加带来的挑战。

Q: HBM4的技术难点?
A: HBM4要用混合键合(Hybrid Bonding)替代微凸块(Micro Bump)，这是全新的工艺，量产至少要到2027年。

Q: 价格走势预判?
A: 短期供不应求，价格坚挺。但2027年产能释放后可能会有价格压力。

Q: 三星和SK海力士的竞争态势?
A: SK海力士领先约6-9个月。三星在HBM4上投入激进，想弯道超车，但成功率存疑。""",
            "snippet": "HBM3E良率80-85%，HBM4需Hybrid Bonding，2027年量产"
        },
        {
            "file_id": 3201,
            "title": "@memoryexpert - HBM供需分析",
            "source_type": "Twitter推文",
            "date": "2026-05-18",
            "author": "@memoryexpert",
            "url": "https://twitter.com/memoryexpert",
            "content": """【HBM供需分析线程 🧵】

1/ HBM供需缺口持续扩大。NVIDIA Blackwell对HBM3E需求量是H100的2.5倍。

2/ SK海力士产能利用率已达105%，三星也在95%以上。供给弹性极低。

3/ 价格走势：HBM3E合约价Q2环比上涨8-10%，Q3预计继续涨5%。

4/ 风险点：如果AI资本开支放缓，2027年可能供过于求。但目前看不到任何放缓迹象。

5/ 投资建议：SK海力士是最纯的HBM标的，三星受手机业务拖累。$000660.KS""",
            "snippet": "HBM供需缺口扩大，合约价Q2环比涨8-10%，SK海力士产能利用率105%"
        },
        {
            "file_id": 3202,
            "title": "存储半导体深度研究",
            "source_type": "Substack",
            "date": "2026-05-12",
            "author": "SemiAnalysis",
            "url": "https://semianalysis.substack.com",
            "content": """【HBM深度：从技术到投资】

技术演进路径：
- HBM2E → HBM3 → HBM3E → HBM4
- 每代带宽提升50-60%，但功耗和良率挑战加剧

供应链瓶颈：
1. TSV（硅通孔）工艺：SK海力士领先
2. 先进封装：台积电CoWoS产能紧张
3. ABF载板：味之素、揖斐电产能跟不上

竞争格局：
- SK海力士：技术领先，与NVIDIA深度绑定
- 三星：追赶中，在NVIDIA供应商认证进度落后
- 美光：第三梯队，专注利基市场

投资观点：
HBM是存储行业最确定的增长点。SK海力士是首选标的。
风险：估值已不便宜，需关注AI资本开支周期变化。""",
            "snippet": "HBM是存储行业最确定增长点，SK海力士技术领先与NVIDIA深度绑定"
        }
    ],

    # =========================================================================
    # 05. AI Agent - Palantir vs Salesforce
    # =========================================================================
    "ai_agent": [
        {
            "file_id": 5001,
            "title": "Palantir AIP Agent产品深度分析",
            "source_type": "AceCampTech",
            "date": "2026-06-22",
            "author": "企业软件研究团队",
            "content": """Palantir AIP (Artificial Intelligence Platform) 集成了Agent功能，
支持自动化工作流。客户反馈AIP能将数据分析效率提升3-5倍，但部署周期长（3-6个月）、
定制化程度高。政府和国防客户接受度高，商业客户仍在观望。""",
            "snippet": "Palantir AIP效率提升3-5x，但部署周期长，政府客户接受度高"
        },
        {
            "file_id": 5002,
            "title": "Salesforce Agentforce产品发布分析",
            "source_type": "AceCampTech",
            "date": "2026-06-20",
            "author": "企业软件研究团队",
            "content": """Salesforce Agentforce是其AI Agent产品，集成在CRM平台中。
主打销售和客服自动化场景，定价按Agent调用次数收费。相比Palantir更标准化，
部署更快，但定制能力较弱。Q1已签约500+企业客户试用。""",
            "snippet": "Salesforce Agentforce主打销售客服自动化，更标准化，500+企业试用"
        },
        {
            "file_id": 5003,
            "title": "@alex_karp关于AI Agent的推文",
            "source_type": "Twitter推文",
            "date": "2026-06-25",
            "author": "alex_karp",
            "url": "https://twitter.com/alex_karp",
            "content": """AI Agents will transform enterprise software. But most are toys.
AIP Agents are battle-tested in the most demanding environments - defense, healthcare, finance.
Real AI requires real data infrastructure. $PLTR""",
            "snippet": "AI Agent将变革企业软件，AIP在最严苛环境中经过实战检验"
        },
        {
            "file_id": 5004,
            "title": "企业AI Agent专家访谈",
            "source_type": "专家访谈",
            "date": "2026-06-18",
            "author": "企业软件专家",
            "content": """当前AI Agent市场处于早期，Palantir和Salesforce代表两种路线：
Palantir走深度定制、高价值客户路线；Salesforce走标准化、规模化路线。
专家判断2026年仍是POC阶段，规模商业化要到2027年。
Palantir技术领先但规模受限，Salesforce规模大但护城河存疑。""",
            "snippet": "AI Agent市场早期，Palantir深度定制、Salesforce标准化，2026仍是POC阶段"
        }
    ],

    # =========================================================================
    # 06. 台积电CoWoS - 封装产能供需
    # =========================================================================
    "tsmc": [
        {
            "file_id": 6001,
            "title": "台积电2026Q1业绩说明会纪要 - CoWoS产能",
            "source_type": "AlphaEngine",
            "date": "2026-06-18",
            "author": "TSMC IR",
            "url": "https://investor.tsmc.com",
            "content": """CoWoS产能2026年将扩产超过100%，但仍无法满足客户需求。
目前订单可见度已排至2026年，NVIDIA、AMD、Google为主要客户。
管理层表示正在加速扩产，预计2026年产能将再翻倍。""",
            "snippet": "CoWoS 2026扩产超100%仍供不应求，订单排至2027年"
        },
        {
            "file_id": 6002,
            "title": "先进封装供应链专家访谈",
            "source_type": "专家访谈",
            "date": "2026-06-15",
            "author": "封装产业专家",
            "content": """台积电CoWoS产能是AI芯片最大瓶颈。实际扩产进度略低于管理层指引，
2026年可能只能达到80-90%扩产。主要限制因素：1）设备交付延迟；2）熟练工人不足；
3）良率爬坡需要时间。专家判断供需紧张将持续到2026年底。""",
            "snippet": "CoWoS实际扩产可能仅80-90%，设备和人工是瓶颈，紧张持续到2026底"
        },
        {
            "file_id": 6003,
            "title": "CoWoS竞争格局分析",
            "source_type": "AceCampTech",
            "date": "2026-06-10",
            "author": "半导体研究团队",
            "content": """台积电CoWoS市场份额超过90%，日月光、Amkor作为替代供应商产能有限。
三星正在开发类似技术但落后2年以上。Intel Foveros主要服务自有产品。
台积电定价能力强，CoWoS毛利率高于先进制程。""",
            "snippet": "台积电CoWoS份额超90%，三星落后2年+，定价能力强"
        },
        {
            "file_id": 6004,
            "title": "@MorrisMark_TSMC关于产能的推文",
            "source_type": "Twitter推文",
            "date": "2026-06-01",
            "author": "MorrisMark_TSMC",
            "url": "https://twitter.com/MorrisMark_TSMC",
            "content": """We are investing heavily in advanced packaging. CoWoS capacity will more than double
in 2026 and double again in 2027. AI demand is unprecedented. We will not let customers down.""",
            "snippet": "CoWoS产能2026翻倍、2027再翻倍，AI需求史无前例"
        }
    ],

    # =========================================================================
    # 07. Tesla/Musk - FSD与xAI
    # =========================================================================
    "tesla": [
        {
            "file_id": 7001,
            "title": "Tesla 2026Q1业绩说明会纪要",
            "source_type": "AlphaEngine",
            "date": "2026-06-23",
            "author": "Tesla IR",
            "url": "https://ir.tesla.com",
            "content": """汽车业务收入同比下降5%，毛利率降至16.8%。FSD V13取得重大进展，
累计行驶里程突破30亿英里。管理层重申Robotaxi将于2026年底在部分城市推出。
储能业务增长强劲，同比+75%。""",
            "snippet": "汽车收入-5%毛利率16.8%，FSD里程破30亿，Robotaxi年底部分城市推出"
        },
        {
            "file_id": 7002,
            "title": "@elonmusk关于FSD和xAI的推文",
            "source_type": "Twitter推文",
            "date": "2026-06-26",
            "author": "elonmusk",
            "url": "https://twitter.com/elonmusk",
            "content": """FSD V13.2 is insane. Approaching human-level driving in most conditions.
Robotaxi will transform transportation and be the biggest asset value increase in history.
xAI's Grok 3 training complete - benchmarks coming soon. $TSLA to the moon!""",
            "snippet": "FSD V13.2接近人类驾驶水平，Robotaxi将是史上最大资产增值，Grok 3训练完成"
        },
        {
            "file_id": 7003,
            "title": "自动驾驶专家访谈 - FSD真实水平评估",
            "source_type": "专家访谈",
            "date": "2026-06-20",
            "author": "自动驾驶专家",
            "content": """FSD V13确有明显进步，但距离L4级别仍有差距。主要问题：极端天气表现差、
复杂路口决策保守、接管率仍高于Waymo。Robotaxi年底推出时间表过于激进，
专家预测可能推迟到2026年中。xAI与Tesla的协同效应尚不清晰。""",
            "snippet": "FSD有进步但距L4仍有差距，Robotaxi可能推迟到2026年中"
        },
        {
            "file_id": 7004,
            "title": "Tesla估值与业务分析",
            "source_type": "AceCampTech",
            "date": "2026-06-15",
            "author": "汽车研究团队",
            "content": """Tesla当前估值中，汽车业务支撑约30%，FSD/Robotaxi约50%，储能约15%，其他5%。
如果Robotaxi延迟，估值将面临显著下修风险。中国市场竞争加剧，Model 3/Y降价压力大。
长期看好储能业务，短期关注Robotaxi进展。""",
            "snippet": "Tesla估值50%来自FSD/Robotaxi，延迟将致估值下修，关注进展"
        }
    ],

    # =========================================================================
    # 08. Anthropic - 估值与融资
    # =========================================================================
    "anthropic": [
        {
            "file_id": 8001,
            "title": "Anthropic最新融资进展分析",
            "source_type": "Substack",
            "date": "2026-06-25",
            "author": "AI研究员",
            "url": "https://airesearch.substack.com",
            "content": """Anthropic据报道正在进行新一轮融资，估值目标400-500亿美元。
Google和Salesforce为主要投资方，Amazon保持现有持股比例。
Claude 3.5表现优异，企业客户增长迅速，ARR据传已达10亿美元。""",
            "snippet": "Anthropic新一轮融资估值目标400-500亿，ARR据传达10亿美元"
        },
        {
            "file_id": 8002,
            "title": "@AnthropicAI关于Claude进展的推文",
            "source_type": "Twitter推文",
            "date": "2026-06-20",
            "author": "AnthropicAI",
            "url": "https://twitter.com/AnthropicAI",
            "content": """Claude is now used by 50% of Fortune 500 companies.
Our focus on AI safety and reliability is resonating with enterprise customers.
Thank you to our amazing team and partners for making this possible.""",
            "snippet": "Claude已被50%财富500强使用，安全可靠性获企业认可"
        },
        {
            "file_id": 8003,
            "title": "AI大模型竞争格局分析",
            "source_type": "AceCampTech",
            "date": "2026-06-18",
            "author": "AI研究团队",
            "content": """Anthropic在企业市场快速增长，Claude 3.5在推理和编程任务上领先。
主要竞争对手：OpenAI（规模最大）、Google（Gemini整合GCP）、Meta（开源路线）。
Anthropic优势：安全性口碑、企业信任度高。劣势：烧钱速度快、缺乏分发渠道。""",
            "snippet": "Anthropic企业市场快速增长，安全性口碑好，但烧钱快缺分发渠道"
        },
        {
            "file_id": 8004,
            "title": "AI初创估值专家访谈",
            "source_type": "专家访谈",
            "date": "2026-06-15",
            "author": "一级市场专家",
            "content": """Anthropic 400-500亿估值意味着40-50x ARR，高于SaaS历史均值但符合AI热度。
关键问题：1）能否持续保持技术领先；2）商业化速度能否跟上烧钱速度；
3）大厂竞争是否会压缩利润空间。专家判断估值合理但风险较高。""",
            "snippet": "Anthropic 400-500亿估值为40-50x ARR，合理但风险高"
        }
    ],

    # =========================================================================
    # 09. SMCI - 审计与财报问题
    # =========================================================================
    "smci": [
        {
            "file_id": 9001,
            "title": "SMCI财报延迟与审计问题跟踪",
            "source_type": "AlphaEngine",
            "date": "2026-06-15",
            "author": "财务分析师",
            "content": """SMCI已聘请新审计师BDO，预计6月底前完成FY2024审计。
公司声明不存在重大财务造假，延迟主要因为内控流程需要加强。
新CFO已上任，正在改善财务报告流程。""",
            "snippet": "SMCI聘请BDO审计，预计6月底完成，公司称无重大财务造假"
        },
        {
            "file_id": 9002,
            "title": "SMCI空头报告深度分析",
            "source_type": "AceCampTech",
            "date": "2026-06-10",
            "author": "财务研究团队",
            "content": """Hindenburg做空报告主要指控：1）关联交易问题；2）收入确认激进；3）出口合规风险。
部分指控有依据，但"财务造假"结论过于绝对。SMCI核心业务（AI服务器）实际需求真实，
关键看审计结果和SEC调查进展。""",
            "snippet": "Hindenburg指控部分有据但造假结论过绝对，关键看审计和SEC调查"
        },
        {
            "file_id": 9003,
            "title": "SMCI供应链专家访谈",
            "source_type": "专家访谈",
            "date": "2026-06-12",
            "author": "服务器行业专家",
            "content": """SMCI在AI服务器市场确有真实业务，与NVIDIA关系紧密。
但公司治理一直是短板，创始人风格激进。专家判断核心业务无虞，
但财务问题可能导致客户观望，短期订单流失风险。Dell和HPE可能受益。""",
            "snippet": "SMCI核心业务真实但治理是短板，财务问题或致客户观望"
        },
        {
            "file_id": 9004,
            "title": "@ABORTEDINCOME关于SMCI的推文",
            "source_type": "Twitter推文",
            "date": "2026-06-18",
            "author": "ABORTEDINCOME",
            "url": "https://twitter.com/ABORTEDINCOME",
            "content": """$SMCI update: New auditor BDO working through the backlog.
June deadline is key. If they miss it again, NASDAQ delisting risk increases.
Position sizing is crucial here - high risk, high reward.""",
            "snippet": "SMCI新审计师BDO处理积压，6月截止日关键，错过则退市风险升高"
        }
    ],

    # =========================================================================
    # 10. 美联储降息影响 - NVDA/MSFT/GOOGL
    # =========================================================================
    "fed_rate": [
        {
            "file_id": 10001,
            "title": "美联储6月FOMC会议纪要解读",
            "source_type": "AlphaEngine",
            "date": "2026-06-12",
            "author": "宏观策略团队",
            "url": "https://federalreserve.gov",
            "content": """美联储维持利率不变，但暗示下半年可能降息1-2次。通胀回落趋势确认，
就业市场有所降温。点阵图显示2026年底利率可能降至4.5-4.75%。
市场对9月首次降息预期升至70%。""",
            "snippet": "美联储暗示下半年降息1-2次，9月首次降息预期70%"
        },
        {
            "file_id": 10002,
            "title": "科技股利率敏感度分析",
            "source_type": "AceCampTech",
            "date": "2026-06-10",
            "author": "策略研究团队",
            "content": """利率下降对科技股整体利好，但影响分化：
NVDA：相对不敏感，业绩驱动为主，降息锦上添花；
MSFT：中等敏感，云业务受益于企业IT支出回暖；
GOOGL：较敏感，广告业务与宏观经济相关性高。
降息25bp预计带动科技板块估值提升3-5%。""",
            "snippet": "降息对NVDA锦上添花、MSFT受益企业IT回暖、GOOGL广告业务受益"
        },
        {
            "file_id": 10003,
            "title": "科技巨头CFO利率表态汇总",
            "source_type": "专家访谈",
            "date": "2026-06-08",
            "author": "企业调研专家",
            "content": """NVIDIA CFO：AI需求与利率关系不大，客户投资AI是战略必须；
Microsoft CFO：降息将刺激中小企业云支出，Azure受益；
Google CFO：宏观环境改善有利广告预算恢复，但竞争压力不减。
专家判断降息对科技股是正面因素，但非核心驱动力。""",
            "snippet": "NVDA称AI需求与利率无关，MSFT Azure受益降息，GOOGL广告预算或恢复"
        },
        {
            "file_id": 10004,
            "title": "@NickTimiraos关于Fed政策的推文",
            "source_type": "Twitter推文",
            "date": "2026-06-15",
            "author": "NickTimiraos",
            "url": "https://twitter.com/NickTimiraos",
            "content": """Fed officials see inflation making 'further progress' toward 2% target.
September rate cut now base case if data cooperates. Tech stocks likely to benefit
from lower discount rates. $NVDA $MSFT $GOOGL watching closely.""",
            "snippet": "Fed官员称通胀进一步向2%靠近，9月降息成基准情形"
        }
    ]
}


# =============================================================================
# Mock Bull/Bear Analysis Results
# =============================================================================

def get_mock_analysis(query: str, search_results: List[Dict]) -> BullBearAnalysis:
    """Get pre-built Bull/Bear analysis for demo queries."""

    query_lower = query.lower()

    # 01. NVIDIA analysis
    if "nvidia" in query_lower or "nvda" in query_lower or "英伟达" in query_lower or "老黄" in query_lower or "黄仁勋" in query_lower:
        return BullBearAnalysis(
            query=query,
            bull_points=[
                Viewpoint(
                    content="数据中心收入263亿美元同比+73%，下季指引280亿超预期，AI需求持续强劲",
                    source="NVIDIA FY2026 Q1业绩说明会",
                    source_type="AlphaEngine",
                    source_date="2026-06-26",
                    confidence="高"
                ),
                Viewpoint(
                    content="Blackwell良率达85%，云厂商订单可见度排到2026Q1，供需紧张持续",
                    source="NVIDIA供应链专家访谈",
                    source_type="专家访谈",
                    source_date="2026-06-25",
                    confidence="高"
                ),
                Viewpoint(
                    content="AI训练GPU市场份额超90%，Blackwell定价提升20-30%客户接受度高",
                    source="GPU定价与竞争格局分析",
                    source_type="AceCampTech",
                    source_date="2026-06-20",
                    confidence="高"
                ),
            ],
            bear_points=[
                Viewpoint(
                    content="台积电CoWoS产能是主要瓶颈，可能限制出货量增长",
                    source="NVIDIA供应链专家访谈",
                    source_type="专家访谈",
                    source_date="2026-06-25",
                    confidence="中"
                ),
                Viewpoint(
                    content="中国市场受限，AMD MI300X在推理市场蚕食份额",
                    source="GPU定价与竞争格局分析",
                    source_type="AceCampTech",
                    source_date="2026-06-20",
                    confidence="中"
                ),
                Viewpoint(
                    content="云厂商自研芯片进度加速，长期可能削弱NVIDIA议价能力",
                    source="GPU定价与竞争格局分析",
                    source_type="AceCampTech",
                    source_date="2026-06-20",
                    confidence="低"
                ),
            ],
            synthesis="NVIDIA在AI芯片市场保持绝对领先，Blackwell架构供不应求，业绩持续超预期。主要瓶颈在于台积电先进封装产能而非需求。中国市场受限和云厂商自研是长期风险，但短期内竞争格局稳固。综合看多。",
            overall_stance="看多",
            key_factors=[
                "Blackwell出货量和CoWoS产能",
                "云厂商AI资本开支持续性",
                "AMD/Intel竞争进展",
                "中国市场政策变化"
            ],
            sources_used=search_results or MOCK_SEARCH_RESULTS.get("nvidia", [])
        )

    # 02. 另类资管 analysis
    if "kkr" in query_lower or "apollo" in query_lower or "blackstone" in query_lower or "另类资管" in query_lower or "资管" in query_lower:
        return BullBearAnalysis(
            query=query,
            bull_points=[
                Viewpoint(
                    content="KKR FRE增速18%最快，AUM突破6010亿，管理层上调全年FRE指引",
                    source="KKR 2026 Q1业绩说明会",
                    source_type="AlphaEngine",
                    source_date="2026-06-02",
                    confidence="高"
                ),
                Viewpoint(
                    content="Blackstone AUM破1.1万亿，全球最大另类资管，基础设施和信贷表现强劲",
                    source="Blackstone 2026 Q1业绩说明会",
                    source_type="AlphaEngine",
                    source_date="2026-05-30",
                    confidence="高"
                ),
                Viewpoint(
                    content="私人信贷和基础设施是增长主力，2026下半年并购活动预计回暖",
                    source="另类资管行业专家访谈",
                    source_type="专家访谈",
                    source_date="2026-06-10",
                    confidence="中"
                ),
            ],
            bear_points=[
                Viewpoint(
                    content="PE退出仍然困难，房地产业务承压",
                    source="Blackstone 2026 Q1业绩说明会",
                    source_type="AlphaEngine",
                    source_date="2026-05-30",
                    confidence="中"
                ),
                Viewpoint(
                    content="Apollo FRE增速12%相对较慢，向多元化资管转型中",
                    source="Apollo 2026 Q1业绩说明会",
                    source_type="AlphaEngine",
                    source_date="2026-06-01",
                    confidence="中"
                ),
                Viewpoint(
                    content="利率高位对估值和并购活动形成压制",
                    source="另类资管行业专家访谈",
                    source_type="专家访谈",
                    source_date="2026-06-10",
                    confidence="中"
                ),
            ],
            synthesis="三大另类资管各有特点：KKR增速最快、Apollo信贷最强、Blackstone规模领先。私人信贷和基础设施成为新增长引擎，PE业务等待并购市场回暖。KKR在增长势头上相对领先，值得关注。",
            overall_stance="中性偏多",
            key_factors=[
                "并购市场回暖时点",
                "利率走势影响估值",
                "私人信贷增长持续性",
                "房地产市场复苏"
            ],
            sources_used=search_results or MOCK_SEARCH_RESULTS.get("kkr", [])
        )

    # 03. Dell analysis
    if "dell" in query_lower or "戴尔" in query_lower:
        return BullBearAnalysis(
            query=query,
            bull_points=[
                Viewpoint(
                    content="ISG收入同比+42%达128亿，AI服务器订单backlog达42亿环比+25%",
                    source="Dell FY26 Q1业绩说明会",
                    source_type="AlphaEngine",
                    source_date="2026-06-27",
                    confidence="高"
                ),
                Viewpoint(
                    content="Dell AI Factory已覆盖85%财富100强企业AI基础设施，企业AI市场领先",
                    source="@MichaelDell推文",
                    source_type="Twitter推文",
                    source_date="2026-06-27",
                    confidence="中"
                ),
                Viewpoint(
                    content="与NVIDIA深度合作，在AI服务器市场份额持续提升",
                    source="服务器产业链专家访谈",
                    source_type="专家访谈",
                    source_date="2026-06-25",
                    confidence="高"
                ),
            ],
            bear_points=[
                Viewpoint(
                    content="ISG毛利率降至18.5%，低于去年同期21.2%，AI服务器拉低整体毛利",
                    source="Dell FY26 Q1业绩说明会",
                    source_type="AlphaEngine",
                    source_date="2026-06-27",
                    confidence="高"
                ),
                Viewpoint(
                    content="竞争加剧，HPE、联想都在抢AI服务器市场，中长期压力大",
                    source="服务器产业链专家访谈",
                    source_type="专家访谈",
                    source_date="2026-06-25",
                    confidence="中"
                ),
                Viewpoint(
                    content="AI PC实际需求仍待观察，溢价能力有限",
                    source="PC市场2026展望",
                    source_type="AceCampTech",
                    source_date="2026-06-15",
                    confidence="中"
                ),
            ],
            synthesis="Dell在AI服务器领域收入强劲增长，订单backlog健康。但AI服务器毛利率较低是核心矛盾——收入增长难以转化为利润增长。需关注毛利率拐点和PC业务企稳。",
            overall_stance="中性偏多",
            key_factors=[
                "AI服务器毛利率能否改善",
                "订单backlog转化为收入的节奏",
                "PC业务何时见底",
                "竞争格局变化"
            ],
            sources_used=search_results or MOCK_SEARCH_RESULTS.get("dell", [])
        )

    # 04. HBM analysis
    if "hbm" in query_lower or "高带宽内存" in query_lower or "海力士" in query_lower:
        return BullBearAnalysis(
            query=query,
            bull_points=[
                Viewpoint(
                    content="SK海力士HBM扩产80%，HBM3E占收入65%，与NVIDIA多年供应协议锁定",
                    source="SK Hynix Strategy Update",
                    source_type="AlphaEngine",
                    source_date="2026-06-15",
                    confidence="高"
                ),
                Viewpoint(
                    content="HBM3E价格环比涨12%，AI需求超预期，封装产能瓶颈支撑价格",
                    source="存储芯片价格与供需分析",
                    source_type="AceCampTech",
                    source_date="2026-06-10",
                    confidence="高"
                ),
                Viewpoint(
                    content="HBM4预计2026Q2量产，SK海力士保持6个月技术领先",
                    source="HBM产业链深度调研",
                    source_type="专家访谈",
                    source_date="2026-06-20",
                    confidence="高"
                ),
            ],
            bear_points=[
                Viewpoint(
                    content="三星HBM3E良率追至75%，差距缩小，获NVIDIA小批量认证",
                    source="三星HBM业务追赶进展",
                    source_type="AceCampTech",
                    source_date="2026-06-18",
                    confidence="中"
                ),
                Viewpoint(
                    content="先进封装产能瓶颈可能限制HBM出货量",
                    source="存储芯片价格与供需分析",
                    source_type="AceCampTech",
                    source_date="2026-06-10",
                    confidence="中"
                ),
                Viewpoint(
                    content="如果AI资本开支放缓，HBM可能面临供过于求风险",
                    source="存储芯片价格与供需分析",
                    source_type="AceCampTech",
                    source_date="2026-06-10",
                    confidence="低"
                ),
            ],
            synthesis="HBM市场由SK海力士主导，与NVIDIA深度绑定。三星良率改善但仍落后，竞争格局短期稳定。HBM4技术迭代将进一步巩固SK海力士领先地位。主要关注封装产能和AI需求持续性。",
            overall_stance="看多",
            key_factors=[
                "AI算力资本开支节奏",
                "三星HBM良率追赶进度",
                "先进封装产能扩张",
                "HBM4量产时间表"
            ],
            sources_used=search_results or MOCK_SEARCH_RESULTS.get("hbm", [])
        )

    # 05. AI Agent analysis
    if "ai agent" in query_lower or "palantir" in query_lower or "salesforce" in query_lower or "agent" in query_lower:
        return BullBearAnalysis(
            query=query,
            bull_points=[
                Viewpoint(
                    content="Palantir AIP效率提升3-5x，在政府和国防客户中接受度高",
                    source="Palantir AIP Agent产品深度分析",
                    source_type="AceCampTech",
                    source_date="2026-06-22",
                    confidence="高"
                ),
                Viewpoint(
                    content="Salesforce Agentforce更标准化，500+企业客户试用，规模化潜力大",
                    source="Salesforce Agentforce产品发布分析",
                    source_type="AceCampTech",
                    source_date="2026-06-20",
                    confidence="中"
                ),
                Viewpoint(
                    content="AI Agent将变革企业软件，Palantir在最严苛环境中经过实战检验",
                    source="@alex_karp推文",
                    source_type="Twitter推文",
                    source_date="2026-06-25",
                    confidence="中"
                ),
            ],
            bear_points=[
                Viewpoint(
                    content="2026年仍是POC阶段，规模商业化要到2027年",
                    source="企业AI Agent专家访谈",
                    source_type="专家访谈",
                    source_date="2026-06-18",
                    confidence="高"
                ),
                Viewpoint(
                    content="Palantir部署周期长（3-6个月），定制化程度高，规模受限",
                    source="Palantir AIP Agent产品深度分析",
                    source_type="AceCampTech",
                    source_date="2026-06-22",
                    confidence="中"
                ),
                Viewpoint(
                    content="Salesforce定制能力弱，护城河存疑",
                    source="企业AI Agent专家访谈",
                    source_type="专家访谈",
                    source_date="2026-06-18",
                    confidence="中"
                ),
            ],
            synthesis="AI Agent市场处于早期，代表两种路线：Palantir深度定制、高价值客户；Salesforce标准化、规模化。短期看Palantir技术领先但规模受限，Salesforce规模大但护城河存疑。2026年仍以POC为主。",
            overall_stance="中性",
            key_factors=[
                "企业AI Agent ROI验证",
                "Palantir商业客户拓展",
                "Salesforce护城河构建",
                "竞争格局演变"
            ],
            sources_used=search_results or MOCK_SEARCH_RESULTS.get("ai_agent", [])
        )

    # 06. 台积电 CoWoS analysis
    if "tsmc" in query_lower or "台积电" in query_lower or "cowos" in query_lower or "封装" in query_lower:
        return BullBearAnalysis(
            query=query,
            bull_points=[
                Viewpoint(
                    content="CoWoS 2026扩产超100%仍供不应求，订单排至2027年，定价能力强",
                    source="台积电2026Q1业绩说明会",
                    source_type="AlphaEngine",
                    source_date="2026-04-18",
                    confidence="高"
                ),
                Viewpoint(
                    content="CoWoS市场份额超90%，三星落后2年+，竞争格局稳固",
                    source="CoWoS竞争格局分析",
                    source_type="AceCampTech",
                    source_date="2026-06-10",
                    confidence="高"
                ),
                Viewpoint(
                    content="CoWoS产能2026翻倍、2027再翻倍，AI需求史无前例",
                    source="@MorrisMark_TSMC推文",
                    source_type="Twitter推文",
                    source_date="2026-06-01",
                    confidence="中"
                ),
            ],
            bear_points=[
                Viewpoint(
                    content="实际扩产可能仅80-90%，设备交付延迟和熟练工人不足是瓶颈",
                    source="先进封装供应链专家访谈",
                    source_type="专家访谈",
                    source_date="2026-06-15",
                    confidence="高"
                ),
                Viewpoint(
                    content="供需紧张将持续到2027年底，可能限制下游AI芯片出货",
                    source="先进封装供应链专家访谈",
                    source_type="专家访谈",
                    source_date="2026-06-15",
                    confidence="中"
                ),
                Viewpoint(
                    content="地缘政治风险，美国推动供应链多元化",
                    source="CoWoS竞争格局分析",
                    source_type="AceCampTech",
                    source_date="2026-06-10",
                    confidence="中"
                ),
            ],
            synthesis="台积电CoWoS是AI芯片最关键瓶颈，市场份额超90%，定价能力极强。管理层指引乐观但实际扩产可能略低于预期。供需紧张格局利好台积电盈利。主要关注扩产执行和地缘政治。",
            overall_stance="看多",
            key_factors=[
                "CoWoS实际扩产进度",
                "设备和人员瓶颈缓解",
                "NVIDIA/AMD需求持续性",
                "地缘政治风险"
            ],
            sources_used=search_results or MOCK_SEARCH_RESULTS.get("tsmc", [])
        )

    # 07. Tesla/Musk analysis
    if "tesla" in query_lower or "特斯拉" in query_lower or "musk" in query_lower or "马斯克" in query_lower or "fsd" in query_lower or "xai" in query_lower:
        return BullBearAnalysis(
            query=query,
            bull_points=[
                Viewpoint(
                    content="FSD V13取得重大进展，累计里程破30亿英里，Robotaxi年底部分城市推出",
                    source="Tesla 2026Q1业绩说明会",
                    source_type="AlphaEngine",
                    source_date="2026-04-23",
                    confidence="中"
                ),
                Viewpoint(
                    content="储能业务同比+75%增长强劲，成为新增长引擎",
                    source="Tesla 2026Q1业绩说明会",
                    source_type="AlphaEngine",
                    source_date="2026-04-23",
                    confidence="高"
                ),
                Viewpoint(
                    content="Musk称FSD V13.2接近人类驾驶水平，xAI Grok 3训练完成",
                    source="@elonmusk推文",
                    source_type="Twitter推文",
                    source_date="2026-06-26",
                    confidence="低"
                ),
            ],
            bear_points=[
                Viewpoint(
                    content="汽车收入-5%毛利率降至16.8%，中国市场竞争加剧",
                    source="Tesla 2026Q1业绩说明会",
                    source_type="AlphaEngine",
                    source_date="2026-04-23",
                    confidence="高"
                ),
                Viewpoint(
                    content="FSD距L4仍有差距，Robotaxi时间表过于激进，可能推迟到2026年中",
                    source="自动驾驶专家访谈",
                    source_type="专家访谈",
                    source_date="2026-06-20",
                    confidence="高"
                ),
                Viewpoint(
                    content="估值50%来自FSD/Robotaxi，若延迟将面临显著下修风险",
                    source="Tesla估值与业务分析",
                    source_type="AceCampTech",
                    source_date="2026-06-15",
                    confidence="高"
                ),
            ],
            synthesis="Tesla当前估值高度依赖FSD/Robotaxi预期（约50%），但专家判断Robotaxi时间表过于激进。汽车业务承压，储能业务是亮点。Musk推文乐观但需警惕兑现风险。xAI协同效应尚不清晰。",
            overall_stance="中性偏空",
            key_factors=[
                "Robotaxi实际推出时间",
                "FSD真实技术水平",
                "汽车毛利率企稳",
                "储能业务增长持续性"
            ],
            sources_used=search_results or MOCK_SEARCH_RESULTS.get("tesla", [])
        )

    # 08. Anthropic analysis
    if "anthropic" in query_lower or "claude" in query_lower:
        return BullBearAnalysis(
            query=query,
            bull_points=[
                Viewpoint(
                    content="新一轮融资估值目标400-500亿，ARR据传达10亿美元，增长迅速",
                    source="Anthropic最新融资进展分析",
                    source_type="Substack",
                    source_date="2026-06-25",
                    confidence="中"
                ),
                Viewpoint(
                    content="Claude已被50%财富500强使用，安全可靠性获企业认可",
                    source="@AnthropicAI推文",
                    source_type="Twitter推文",
                    source_date="2026-06-20",
                    confidence="中"
                ),
                Viewpoint(
                    content="Claude 3.5在推理和编程任务上领先，企业市场快速增长",
                    source="AI大模型竞争格局分析",
                    source_type="AceCampTech",
                    source_date="2026-06-18",
                    confidence="高"
                ),
            ],
            bear_points=[
                Viewpoint(
                    content="400-500亿估值为40-50x ARR，高于SaaS历史均值，风险较高",
                    source="AI初创估值专家访谈",
                    source_type="专家访谈",
                    source_date="2026-06-15",
                    confidence="高"
                ),
                Viewpoint(
                    content="烧钱速度快，缺乏分发渠道，商业化速度能否跟上是问题",
                    source="AI大模型竞争格局分析",
                    source_type="AceCampTech",
                    source_date="2026-06-18",
                    confidence="中"
                ),
                Viewpoint(
                    content="大厂竞争（OpenAI、Google、Meta）可能压缩利润空间",
                    source="AI初创估值专家访谈",
                    source_type="专家访谈",
                    source_date="2026-06-15",
                    confidence="中"
                ),
            ],
            synthesis="Anthropic凭借Claude的技术领先和安全性口碑在企业市场快速增长。但400-500亿估值意味着高预期，需要持续证明商业化能力。作为非上市公司，关注其技术迭代和ARR增长。",
            overall_stance="中性偏多",
            key_factors=[
                "ARR增长和商业化速度",
                "技术领先能否持续",
                "与大厂竞争格局",
                "融资和估值走势"
            ],
            sources_used=search_results or MOCK_SEARCH_RESULTS.get("anthropic", [])
        )

    # 09. SMCI analysis
    if "smci" in query_lower or "超微" in query_lower or "super micro" in query_lower:
        return BullBearAnalysis(
            query=query,
            bull_points=[
                Viewpoint(
                    content="已聘请BDO审计，预计6月底完成，公司声明无重大财务造假",
                    source="SMCI财报延迟与审计问题跟踪",
                    source_type="AlphaEngine",
                    source_date="2026-06-15",
                    confidence="中"
                ),
                Viewpoint(
                    content="核心AI服务器业务真实，与NVIDIA关系紧密，需求确实存在",
                    source="SMCI供应链专家访谈",
                    source_type="专家访谈",
                    source_date="2026-06-12",
                    confidence="高"
                ),
                Viewpoint(
                    content="Hindenburg指控造假结论过于绝对，部分指控有据但非定论",
                    source="SMCI空头报告深度分析",
                    source_type="AceCampTech",
                    source_date="2026-06-10",
                    confidence="中"
                ),
            ],
            bear_points=[
                Viewpoint(
                    content="6月截止日关键，若再次错过NASDAQ退市风险升高",
                    source="@ABORTEDINCOME推文",
                    source_type="Twitter推文",
                    source_date="2026-06-18",
                    confidence="高"
                ),
                Viewpoint(
                    content="公司治理是短板，财务问题可能导致客户观望，短期订单流失",
                    source="SMCI供应链专家访谈",
                    source_type="专家访谈",
                    source_date="2026-06-12",
                    confidence="高"
                ),
                Viewpoint(
                    content="关联交易、收入确认激进、出口合规风险仍待审计确认",
                    source="SMCI空头报告深度分析",
                    source_type="AceCampTech",
                    source_date="2026-06-10",
                    confidence="中"
                ),
            ],
            synthesis="SMCI核心业务真实但治理和财务报告问题严重。6月审计截止日是关键节点，通过则利空出尽，未通过则退市风险上升。高风险高回报标的，适合风险承受能力强的投资者。",
            overall_stance="中性偏空",
            key_factors=[
                "6月底审计结果",
                "SEC调查进展",
                "客户订单是否流失",
                "退市风险评估"
            ],
            sources_used=search_results or MOCK_SEARCH_RESULTS.get("smci", [])
        )

    # 10. 美联储/降息影响 analysis
    if "fed" in query_lower or "美联储" in query_lower or "降息" in query_lower or "利率" in query_lower:
        return BullBearAnalysis(
            query=query,
            bull_points=[
                Viewpoint(
                    content="美联储暗示下半年降息1-2次，9月首次降息预期升至70%",
                    source="美联储6月FOMC会议纪要解读",
                    source_type="AlphaEngine",
                    source_date="2026-06-12",
                    confidence="高"
                ),
                Viewpoint(
                    content="降息对NVDA锦上添花，MSFT Azure受益企业IT回暖，GOOGL广告预算恢复",
                    source="科技股利率敏感度分析",
                    source_type="AceCampTech",
                    source_date="2026-06-10",
                    confidence="高"
                ),
                Viewpoint(
                    content="降息25bp预计带动科技板块估值提升3-5%",
                    source="科技股利率敏感度分析",
                    source_type="AceCampTech",
                    source_date="2026-06-10",
                    confidence="中"
                ),
            ],
            bear_points=[
                Viewpoint(
                    content="NVIDIA CFO称AI需求与利率关系不大，降息非核心驱动力",
                    source="科技巨头CFO利率表态汇总",
                    source_type="专家访谈",
                    source_date="2026-06-08",
                    confidence="中"
                ),
                Viewpoint(
                    content="降息幅度可能有限，年底利率仍在4.5-4.75%",
                    source="美联储6月FOMC会议纪要解读",
                    source_type="AlphaEngine",
                    source_date="2026-06-12",
                    confidence="中"
                ),
                Viewpoint(
                    content="GOOGL广告业务竞争压力不减，降息不能解决结构性问题",
                    source="科技巨头CFO利率表态汇总",
                    source_type="专家访谈",
                    source_date="2026-06-08",
                    confidence="中"
                ),
            ],
            synthesis="降息对科技股整体利好但影响分化：NVDA业绩驱动为主，利率敏感度低；MSFT受益于企业IT支出回暖；GOOGL与宏观相关性高。降息是正面因素但非决定性因素，基本面仍是核心。",
            overall_stance="中性偏多",
            key_factors=[
                "9月降息是否落地",
                "降息幅度和节奏",
                "各公司基本面差异",
                "宏观经济整体走势"
            ],
            sources_used=search_results or MOCK_SEARCH_RESULTS.get("fed_rate", [])
        )

    # Default fallback
    return BullBearAnalysis(
        query=query,
        bull_points=[
            Viewpoint(
                content="暂无明确看多观点，需要更多数据支持",
                source="系统提示",
                source_type="",
                source_date="",
                confidence="低"
            )
        ],
        bear_points=[
            Viewpoint(
                content="暂无明确看空观点，需要更多数据支持",
                source="系统提示",
                source_type="",
                source_date="",
                confidence="低"
            )
        ],
        synthesis="当前问题没有预置的分析数据，请尝试以下问题：NVIDIA业绩、KKR/Apollo/Blackstone资管对比、Dell AI服务器、HBM扩产、AI Agent、台积电CoWoS、Tesla FSD、Anthropic估值、SMCI审计、美联储降息影响",
        overall_stance="中性",
        key_factors=["请尝试预置问题获取完整分析"],
        sources_used=search_results or []
    )


def get_mock_search_results(query: str) -> List[Dict]:
    """Get mock search results for a query."""
    query_lower = query.lower()

    # 01. NVIDIA
    if "nvidia" in query_lower or "nvda" in query_lower or "英伟达" in query_lower or "老黄" in query_lower or "黄仁勋" in query_lower:
        return MOCK_SEARCH_RESULTS["nvidia"]
    # 02. 另类资管
    elif "kkr" in query_lower or "apollo" in query_lower or "blackstone" in query_lower or "另类资管" in query_lower or "资管" in query_lower:
        return MOCK_SEARCH_RESULTS["kkr"]
    # 03. Dell
    elif "dell" in query_lower or "戴尔" in query_lower:
        return MOCK_SEARCH_RESULTS["dell"]
    # 04. HBM
    elif "hbm" in query_lower or "海力士" in query_lower or "扩产" in query_lower or "高带宽内存" in query_lower:
        return MOCK_SEARCH_RESULTS["hbm"]
    # 05. AI Agent
    elif "ai agent" in query_lower or "palantir" in query_lower or "salesforce" in query_lower or "agent" in query_lower:
        return MOCK_SEARCH_RESULTS["ai_agent"]
    # 06. 台积电 CoWoS
    elif "tsmc" in query_lower or "台积电" in query_lower or "cowos" in query_lower or "封装" in query_lower:
        return MOCK_SEARCH_RESULTS["tsmc"]
    # 07. Tesla/Musk
    elif "tesla" in query_lower or "特斯拉" in query_lower or "musk" in query_lower or "马斯克" in query_lower or "fsd" in query_lower or "xai" in query_lower:
        return MOCK_SEARCH_RESULTS["tesla"]
    # 08. Anthropic
    elif "anthropic" in query_lower or "claude" in query_lower:
        return MOCK_SEARCH_RESULTS["anthropic"]
    # 09. SMCI
    elif "smci" in query_lower or "超微" in query_lower or "super micro" in query_lower:
        return MOCK_SEARCH_RESULTS["smci"]
    # 10. 美联储/降息
    elif "fed" in query_lower or "美联储" in query_lower or "降息" in query_lower or "利率" in query_lower:
        return MOCK_SEARCH_RESULTS["fed_rate"]
    else:
        return []
