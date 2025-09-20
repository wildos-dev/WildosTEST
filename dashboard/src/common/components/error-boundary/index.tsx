import * as React from 'react';
import { Button } from '@wildosvpn/common/components/ui';
import { Icon } from '@wildosvpn/common/components/ui/icon';
import { useTranslation } from 'react-i18next';

interface Props {
  children?: React.ReactNode;
  fallback?: React.ReactNode;
  onReset?: () => void;
}

interface State {
  hasError: boolean;
  error?: Error;
  errorInfo?: React.ErrorInfo;
}

export class ErrorBoundary extends React.Component<Props, State> {
  public state: State = {
    hasError: false
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    
    this.setState({
      error,
      errorInfo
    });

    // Log to external service if configured
    if (typeof window !== 'undefined' && (window as any).logError) {
      (window as any).logError(error, errorInfo);
    }
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: undefined, errorInfo: undefined });
    this.props.onReset?.();
  };

  private handleGoHome = () => {
    window.location.href = '/';
  };

  public render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <ErrorFallback
          error={this.state.error}
          errorInfo={this.state.errorInfo}
          onReset={this.handleReset}
          onGoHome={this.handleGoHome}
        />
      );
    }

    return this.props.children;
  }
}

interface ErrorFallbackProps {
  error?: Error;
  errorInfo?: React.ErrorInfo;
  onReset: () => void;
  onGoHome: () => void;
}

function ErrorFallback({ error, errorInfo, onReset, onGoHome }: ErrorFallbackProps) {
  const { t } = useTranslation();
  const isDev = import.meta.env.DEV;

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-900 p-4">
      <div className="max-w-md w-full bg-slate-800 rounded-lg shadow-xl p-6">
        <div className="text-center">
          <Icon name="AlertCircle" className="mx-auto h-12 w-12 text-destructive mb-4" />
          <h1 className="text-xl font-semibold text-slate-100 mb-2">
            {t('error.something_went_wrong')}
          </h1>
          <p className="text-slate-400 mb-6">
            {t('error.unexpected_error_description')}
          </p>

          {isDev && error && (
            <div className="mb-6 p-4 bg-slate-700 rounded-md text-left">
              <h3 className="text-sm font-medium text-slate-200 mb-2">{t('error.details')}:</h3>
              <pre className="text-xs text-slate-400 whitespace-pre-wrap overflow-auto max-h-32">
                {error.name}: {error.message}
                {error.stack && `\n\nStack trace:\n${error.stack}`}
                {errorInfo?.componentStack && `\n\nComponent stack:${errorInfo.componentStack}`}
              </pre>
            </div>
          )}

          <div className="flex gap-3 justify-center">
            <Button
              onClick={onReset}
              variant="default"
              size="sm"
              className="flex items-center gap-2"
              data-testid="button-retry"
            >
              <Icon name="RefreshCw" className="h-4 w-4" />
              {t('error.try_again')}
            </Button>
            <Button
              onClick={onGoHome}
              variant="outline"
              size="sm"
              className="flex items-center gap-2"
              data-testid="button-home"
            >
              <Icon name="Home" className="h-4 w-4" />
              {t('home')}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

// Hook version for functional components
interface ErrorBoundaryState {
  hasError: boolean;
  error?: Error;
}

export function useErrorBoundary() {
  const [state, setState] = React.useState<ErrorBoundaryState>({ hasError: false });

  const resetError = () => setState({ hasError: false, error: undefined });
  
  const captureError = (error: Error) => {
    console.error('Error captured:', error);
    setState({ hasError: true, error });
  };

  React.useEffect(() => {
    const handleError = (event: ErrorEvent) => {
      captureError(new Error(event.message));
    };

    const handleUnhandledRejection = (event: PromiseRejectionEvent) => {
      captureError(new Error(event.reason));
    };

    window.addEventListener('error', handleError);
    window.addEventListener('unhandledrejection', handleUnhandledRejection);

    return () => {
      window.removeEventListener('error', handleError);
      window.removeEventListener('unhandledrejection', handleUnhandledRejection);
    };
  }, []);

  return { hasError: state.hasError, error: state.error, resetError, captureError };
}

export default ErrorBoundary;