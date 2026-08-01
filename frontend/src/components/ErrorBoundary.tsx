import { Component, type ReactNode } from "react";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback;
      return (
        <div className="flex flex-col items-center justify-center min-h-[60vh] text-center px-4">
          <div className="text-5xl mb-4">&#9888;&#65039;</div>
          <h2 className="text-xl font-bold text-ink mb-2">页面出现异常</h2>
          <p className="text-ink-secondary mb-6 max-w-md">
            {this.state.error?.message || "发生了未知错误，请刷新页面重试"}
          </p>
          <button
            onClick={() => {
              this.setState({ hasError: false, error: null });
              window.location.reload();
            }}
            className="px-6 py-2 bg-brand-600 text-white rounded-lg hover:bg-brand-700 transition-colors"
          >
            刷新页面
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
