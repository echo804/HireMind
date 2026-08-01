# HireMind 设计规范（Design System）— 极简素蓝白

> 版本：v1.0 ｜ 适用范围：`frontend/` 全部页面与组件 ｜ 配套 skill：`/hiremind-design-system`（开发检查清单）
> 状态：**规范已定，待实施**。实施时需同步更新 `.reasonix/skills/hiremind-design-system/SKILL.md` 与代码。

---

## 1. 设计原则（总纲）

1. **素蓝白**：暖白底 + 单一深蓝 + 灰阶。蓝色只在 CTA、激活态、链接、品牌名出现，其余全部灰阶。
2. **单一强调色**：一屏内只允许出现一个强调色（brand 蓝）；语义色（success/error/warning）只表达状态，不参与装饰。
3. **排印优先**：层级来自字重 / 字号 / 字距，禁止"艺术字特效"（阴影、描边、渐变字）。
4. **动效克制**：动效只服务状态切换与首次进入；欢迎页拼写动画只播一次；尊重 `prefers-reduced-motion`。
5. **中英混排**：英文/数字用 Inter（品牌名 HireMind 用 Display 层级）；中文用系统黑体（PingFang SC / MiSans / Microsoft YaHei），不引艺术字体。
6. **图标纪律**：图标一律用 `lucide-react`（1.5px 线性）；禁止 emoji 作图标。

---

## 2. 现状盘点（改造面）

### 2.1 emoji 使用点（14 处，全部需替换）

| 位置 | emoji | 替换方案 |
|---|---|---|
| `Home.tsx:45` 未登录 hero 图标 | 🎯 | `Target`（欢迎页改造后此分支整体移除） |
| `Home.tsx:62/67/72` 功能卡 | 📄 🤖 📚 | `FileText` `Bot` `BookOpen` |
| `Home.tsx:83-86` 统计卡 | 📄 📝 📅 📚 | `FileText` `ClipboardList` `Calendar` `BookOpen` |
| `Home.tsx:90-92` 快捷操作 | 📄 🤖 📚 | 同上 |
| `Home.tsx:99` 欢迎语 | 👋 | 删除（纯文字） |
| `Home.tsx:145` 空态 | 🚀 | `Rocket`（线性） |
| `InterviewReport.tsx:245` 优势项 | ✓ | `CheckCircle2` |
| `InterviewReport.tsx:259` 导出 PDF | 📄 | `FileDown` |
| `InterviewReport.tsx:263` 重新评估 | 🔄 | `RefreshCw` |
| `KnowledgeBase.tsx:197` 文件类型 | 📫 📑 📩 | `FileText` `FileType2` `File` |
| `ResumeDetail.tsx:280` 步骤指示 | ✓ ● ○ | `CheckCircle2` `Circle`（或保留符号，规范允许） |

### 2.2 硬编码色值（改造面）

- **slate 灰阶文字 140+ 处**（`text-slate-800/700/600/500/400`）→ 映射 `ink` 令牌
- **blue-* 默认类约 70 处**（`bg-blue-600`、`text-blue-600`、`ring-blue-500` 等）→ 统一 `brand-*` 令牌（当前 `index.css:4-15` 已定义 brand 阶梯但业务代码未使用——**双蓝并存是首要治理对象**）
- **语义色约 50 处**（red/green/yellow）→ 语义令牌映射
- **散落 hex 10 余个**（`#e2e8f0`、`#16a34a`、`#2563eb`、`#dc2626`、`#ca8a04` 等）→ 归入令牌

---

## 3. 设计令牌（Design Tokens）

### 3.1 色彩

```css
@theme {
  /* 底色 */
  --color-paper: #FAFAF9;          /* 页面底（暖白） */
  --color-surface: #FFFFFF;        /* 卡片 / 浮层 */
  --color-surface-muted: #F5F5F4;  /* 次级底 / 悬停底 */

  /* 文字灰阶 */
  --color-ink: #18181B;            /* 主文 */
  --color-ink-secondary: #52525B;  /* 次文 */
  --color-ink-muted: #A1A1AA;      /* 弱化 / 占位 */
  --color-ink-disabled: #D4D4D8;   /* 禁用 */

  /* 边框 */
  --color-line: #E4E4E7;           /* hairline 边框 */

  /* 品牌蓝（沿用现有 brand 阶梯，主色收敛到 600/700） */
  --color-brand-50: #EFF6FF;
  --color-brand-100: #DBEAFE;
  --color-brand-500: #3B82F6;
  --color-brand-600: #2563EB;      /* 主 CTA */
  --color-brand-700: #1D4ED8;      /* hover / 品牌名 */
  --color-brand-800: #1E40AF;
  --color-brand-900: #1E3A8A;

  /* 语义色（只表达状态） */
  --color-success: #16A34A;
  --color-warning: #CA8A04;
  --color-error: #DC2626;

  /* 字体 */
  --font-sans: "Inter", "PingFang SC", "Microsoft YaHei", system-ui, sans-serif;
}
```

**旧类映射规则**（实施时全局替换）：

| 旧 | 新 |
|---|---|
| `text-slate-800` / `text-slate-700` | `text-ink` |
| `text-slate-600` / `text-slate-500` | `text-ink-secondary` |
| `text-slate-400` | `text-ink-muted` |
| `bg-slate-100` / `bg-slate-50` | `bg-surface-muted` |
| `border-slate-200` / `border-slate-300` / `border-slate-100` | `border-line` |
| `bg-blue-600` / `text-blue-600` / `ring-blue-500` 等全部 blue-* | 对应 `brand-*` |
| `bg-green-*` / `bg-red-*` / `bg-yellow-*` 浅底 | `bg-success/10` 类浅底语义 |
| 页面底色 `#f8fafc` / `#f1f5f9` | `bg-paper` |

### 3.2 字体排印阶梯

| 层级 | 规格 | 用途 |
|---|---|---|
| Display | `text-5xl~7xl font-bold tracking-tight` | 品牌名 HireMind（欢迎页） |
| 页面标题 | `text-2xl font-semibold tracking-tight` | 「简历管理」「模拟面试」等 |
| 功能名 | `text-lg font-semibold tracking-wide` | 卡片标题、导航强调项 |
| 正文 | `text-sm/base font-normal text-ink-secondary leading-relaxed` | 描述、内容 |
| 辅助 | `text-xs text-ink-muted` | 时间戳、次要信息 |

字体加载：`@fontsource/inter` 按字重 import（400/500/600/700）；中文走系统栈。**禁止**：花哨艺术字体、艺术字特效。

### 3.3 几何

- 卡片：`rounded-xl`（12px）+ `border border-line`（hairline）+ `shadow-card`（沿用现有极浅阴影）
- 控件：按钮 / 输入 `rounded-lg`（8px）
- 徽标：`rounded-full` 胶囊，浅底语义色
- 间距：4px 基数阶梯；页面容器 `px-4/6/8`，区块间距 `mb-4/6/8`

### 3.4 动效

- 过渡：`transition-all duration-150~300 ease-out`
- hover/active：卡片 `-translate-y-0.5 + shadow-card-hover`；按钮沿用 `btn-primary` 现有（hover 变色、`active:scale-[0.98]`）
- 欢迎页拼写：`useTypewriter`（见 §5），只播一次，光标 `animate-blink`
- 全局降级：

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

**禁止**：循环动画、马卡龙渐变卡、装饰性动画、文字贴图 PNG。

---

## 4. 页面应用规范

### 4.1 欢迎页（登录前首页 `/`）

- **结构**：独立全屏，不套 `Layout` 外壳（复用 `Layout.tsx:22-24` 对 `/login`、`/register` 的放行机制；`App.tsx` 拆分 `/` 未登录分支）
- **背景**：`bg-paper` 纯色 + 极淡蓝光晕（`radial-gradient(600px 300px at 50% 40%, rgb(37 99 235 / 0.05), transparent 70%)`）
- **中央**：`HireMind` 动态拼写（Display 层级 `text-5xl md:text-7xl font-bold tracking-tight text-brand-700 select-none`）+ blink 光标
- **副语**：蓝色小字 `text-sm md:text-base text-brand-500 tracking-wide mt-6`，一句话介绍，如「让每一次面试，都有备而来」
- **时序**：`startDelay 400ms` → `speed 80ms/字` → `done` 后副语与 CTA（登录 / 注册，`btn-primary` / `btn-secondary`）以 `opacity 300ms` 淡入
- **降级**：`prefers-reduced-motion` 时直接全显，无动画
- **响应式**：字号降级、CTA 全宽（移动端）

### 4.2 登录后功能页

- **emoji 替换**：按 §2.1 对照表全部替换为 lucide 图标（`w-4/5/6`、`strokeWidth={1.5}`、`currentColor`）
- **页面标题**：`text-2xl font-semibold tracking-tight text-ink`
- **导航**：`text-sm font-medium`，激活态 `text-brand-600 + border-b-2 border-brand-600`（沿用现有 Layout 结构）
- **卡片**：`bg-surface border border-line rounded-xl p-5 shadow-card`（替换 `card` 类的 `bg-white border-slate-100`）
- **按钮**：沿用 `btn-primary` / `btn-secondary` / `btn-danger`（色值随令牌更新）
- **徽标**：浅底语义色胶囊（`bg-brand-50 text-brand-700` 等，删除 emoji）
- **空态**：lucide 线性图标 + `text-ink-muted` 文案，禁止 emoji 插图

---

## 5. 实现映射代码片段

### 5.1 `useTypewriter` hook（`frontend/src/hooks/useTypewriter.ts`）

```ts
import { useEffect, useState } from "react";

export function useTypewriter(text: string, speed = 80, startDelay = 400) {
  const [displayed, setDisplayed] = useState("");
  const [done, setDone] = useState(false);

  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      setDisplayed(text);
      setDone(true);
      return;
    }
    let i = 0;
    let timer: number | undefined;
    const start = window.setTimeout(() => {
      timer = window.setInterval(() => {
        i += 1;
        setDisplayed(text.slice(0, i));
        if (i >= text.length) {
          window.clearInterval(timer);
          setDone(true);
        }
      }, speed);
    }, startDelay);
    return () => {
      window.clearTimeout(start);
      if (timer !== undefined) window.clearInterval(timer);
    };
  }, [text, speed, startDelay]);

  return { displayed, done };
}
```

### 5.2 blink 光标（`index.css`）

```css
@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}
.animate-blink { animation: blink 1s step-end infinite; }
```

### 5.3 欢迎页骨架

```tsx
export default function Welcome() {
  const { displayed, done } = useTypewriter("HireMind");
  return (
    <div className="min-h-screen bg-paper flex flex-col items-center justify-center gap-6 px-6">
      <h1 className="text-5xl md:text-7xl font-bold tracking-tight text-brand-700 select-none">
        {displayed}
        {!done && (
          <span className="inline-block w-[3px] h-[1em] bg-brand-700 align-middle ml-1 animate-blink" />
        )}
      </h1>
      <p className={`text-sm md:text-base text-brand-500 tracking-wide transition-opacity duration-300 ${done ? "opacity-100" : "opacity-0"}`}>
        让每一次面试，都有备而来
      </p>
      <div className={`flex gap-3 transition-opacity duration-300 ${done ? "opacity-100" : "opacity-0"}`}>
        <Link to="/login" className="btn-primary">登录</Link>
        <Link to="/register" className="btn-secondary">注册</Link>
      </div>
    </div>
  );
}
```

### 5.4 依赖安装

```bash
cd frontend
npm install lucide-react@^1.28.0 @fontsource/inter@^5.3.0
```

`main.tsx` 引入字体：`import "@fontsource/inter/400.css"; import "@fontsource/inter/500.css"; import "@fontsource/inter/600.css"; import "@fontsource/inter/700.css";`

---

## 6. 实施顺序建议

1. **基建**：安装依赖 → `index.css` 令牌更新（§3.1）+ 字体引入 + blink keyframes
2. **全局替换**：色值映射（§3.1 表格）→ emoji 替换（§2.1 对照表）→ 更新 skill 为最终版
3. **欢迎页**：新建 `hooks/useTypewriter.ts` + 欢迎页组件 + 路由拆分（§4.1 / §5.3）
4. **回归**：全页面走查（对比度、禁用态、reduced-motion）、`npm run build` 通过

---

*规范 v1.0 生成于设计评估会话；现状数据来自 `frontend/src` 实际扫描。*
