import * as React from 'react';
import { Icon } from '@wildosvpn/common/components/ui/icon';
import { toast } from 'sonner';
import { useNavigate } from '@tanstack/react-router';
import { useTranslation } from 'react-i18next';
import i18n from '@wildosvpn/features/i18n';
import { Button } from '@wildosvpn/common/components/ui/button';
import { Alert, AlertTitle, AlertDescription } from '@wildosvpn/common/components/ui/alert';

interface ErrorBoundaryState {
  hasError: boolean;
  error?: Error;
  errorInfo?: React.ErrorInfo;
}

interface ErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
  showToast?: boolean;
  resetKeys?: Array<string | number>;
  resetOnPropsChange?: boolean;
}

export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  private resetTimeoutId: number | null = null;

  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    this.setState({ error, errorInfo });

    // Show toast notification
    if (this.props.showToast !== false) {
      toast.error(i18n.t('error.component_error'), {
        description: i18n.t('error.component_crashed_refresh'),
        duration: 8000
      });
    }

    // Call custom error handler
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }

    // Log error for debugging
    console.error('ErrorBoundary caught an error:', error, errorInfo);
  }

  componentDidUpdate(prevProps: ErrorBoundaryProps) {
    const { resetKeys = [], resetOnPropsChange = true } = this.props;
    const { hasError } = this.state;

    if (hasError && resetOnPropsChange) {
      const hasResetKeyChanged = resetKeys.some(
        (key, i) => prevProps.resetKeys?.[i] !== key
      );

      if (hasResetKeyChanged) {
        this.resetErrorBoundary();
      }
    }
  }

  resetErrorBoundary = () => {
    if (this.resetTimeoutId) {
      clearTimeout(this.resetTimeoutId);
    }

    this.resetTimeoutId = window.setTimeout(() => {
      this.setState({ hasError: false, error: undefined, errorInfo: undefined });
    }, 100);
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return <ErrorFallback onReset={this.resetErrorBoundary} error={this.state.error} />;
    }

    return this.props.children;
  }
}

interface ErrorFallbackProps {
  onReset?: () => void;
  error?: Error;
}

export const ErrorFallback: React.FC<ErrorFallbackProps> = ({ onReset, error }) => {
  const navigate = useNavigate();
  const { t } = useTranslation();
  
  const handleGoHome = () => {
    navigate({ to: '/' });
  };

  return (
    <div className="flex items-center justify-center min-h-[200px] p-4">
      <div className="max-w-md w-full">
        <Alert variant="destructive">
          <Icon name="AlertTriangle" className="h-4 w-4" />
          <AlertTitle>{t('error.something_went_wrong')}</AlertTitle>
          <AlertDescription className="space-y-4">
            <p>{t('error.component_crashed')}</p>
            
            {error && (
              <details className="mt-2">
                <summary className="cursor-pointer text-sm opacity-70">
                  {t('error.technical_details')}
                </summary>
                <pre className="mt-2 text-xs bg-muted p-2 rounded overflow-auto max-h-32">
                  {error.message}
                </pre>
              </details>
            )}

            <div className="flex gap-2 pt-2">
              {onReset && (
                <Button
                  onClick={onReset}
                  variant="outline"
                  size="sm"
                  className="flex items-center gap-2"
                >
                  <Icon name="RefreshCw" className="h-3 w-3" />
                  {t('buttons.try_again')}
                </Button>
              )}
              <Button
                onClick={handleGoHome}
                variant="default"
                size="sm"
                className="flex items-center gap-2"
              >
                <Icon name="Home" className="h-3 w-3" />
                {t('buttons.go_home')}
              </Button>
            </div>
          </AlertDescription>
        </Alert>
      </div>
    </div>
  );
};

// Widget-specific error boundary with optimized fallback
interface WidgetErrorBoundaryProps extends Omit<ErrorBoundaryProps, 'fallback'> {
  widgetName?: string;
  showFallbackContent?: boolean;
}

export const WidgetErrorBoundary: React.FC<WidgetErrorBoundaryProps> = ({
  widgetName = 'Widget',
  showFallbackContent = true,
  children,
  ...props
}) => {
  const [resetKey, setResetKey] = React.useState(0);
  const { t } = useTranslation();
  
  const handleRefresh = () => {
    setResetKey(prev => prev + 1);
  };

  const fallback = showFallbackContent ? (
    <div className="flex items-center justify-center min-h-[150px] p-4 border border-dashed border-muted-foreground/30 rounded-lg">
      <div className="text-center">
        <Icon name="AlertTriangle" className="h-8 w-8 text-muted-foreground mx-auto mb-2" />
        <p className="text-sm text-muted-foreground">{widgetName} {t('status.temporarily_unavailable')}</p>
        <Button
          variant="ghost"
          size="sm"
          onClick={handleRefresh}
          className="mt-2"
        >
          <Icon name="RefreshCw" className="h-3 w-3 mr-1" />
          {t('buttons.refresh')}
        </Button>
      </div>
    </div>
  ) : null;

  return (
    <ErrorBoundary fallback={fallback} showToast={false} resetKeys={[resetKey]} {...props}>
      {children}
    </ErrorBoundary>
  );
};