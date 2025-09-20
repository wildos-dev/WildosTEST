import * as React from 'react'
import ReactDOM from 'react-dom/client'
import { RouterProvider, createHashHistory, createRouter } from '@tanstack/react-router'
import './globals.css'

import { routeTree } from './routeTree.gen'
import { ErrorBoundary } from '@wildosvpn/common/components/error-boundary'

// Secure error logging system with DEV/PROD separation
let isLogging = false; // Flag to prevent recursion

const ErrorLogger = {
    logError(category: string, error: any, extra?: any) {
        if (isLogging) return; // Prevent recursion
        
        isLogging = true;
        const timestamp = new Date().toISOString();
        
        try {
            if (import.meta.env.DEV) {
                // DEV: Full detailed logging with sensitive data
                const errorData = {
                    timestamp,
                    category,
                    message: error?.message || error,
                    stack: error?.stack,
                    userAgent: navigator.userAgent,
                    url: window.location.href,
                    ...extra
                };

                console.group(`🔴 ${category} [${timestamp}]`);
                console.error('Error Data:', errorData);
                if (error?.stack) {
                    console.trace('Stack Trace:');
                }
                console.groupEnd();

                // Store in localStorage only in DEV
                try {
                    const storedErrors = JSON.parse(localStorage.getItem('dashboard-errors') || '[]');
                    storedErrors.push(errorData);
                    // Keep only last 50 errors
                    if (storedErrors.length > 50) storedErrors.shift();
                    localStorage.setItem('dashboard-errors', JSON.stringify(storedErrors));
                } catch (e) {
                    console.warn('Failed to store error in localStorage:', e);
                }
            } else {
                // PROD: Minimal logging without sensitive data
                const safeErrorData = {
                    timestamp,
                    category,
                    message: error?.message || 'Application error occurred',
                    type: error?.name || 'Error'
                };

                // Only log critical errors in production
                if (this.isCriticalError(category)) {
                    console.error(`Application Error [${category}]:`, safeErrorData.message);
                }
            }
        } finally {
            isLogging = false;
        }
    },

    isCriticalError(category: string): boolean {
        const criticalCategories = [
            'REACT_ERROR_BOUNDARY',
            'REACT_MOUNT_ERROR', 
            'APP_INIT_ERROR',
            'APP_INITIALIZATION_ERROR',
            'GLOBAL_ERROR'
        ];
        return criticalCategories.includes(category);
    },

    // DEV-only methods
    clearStoredErrors() {
        if (import.meta.env.DEV) {
            localStorage.removeItem('dashboard-errors');
            console.log('✅ Stored errors cleared');
        }
    },

    getStoredErrors() {
        if (import.meta.env.DEV) {
            try {
                return JSON.parse(localStorage.getItem('dashboard-errors') || '[]');
            } catch {
                return [];
            }
        }
        return [];
    },

    printStoredErrors() {
        if (import.meta.env.DEV) {
            const errors = this.getStoredErrors();
            console.log('📋 Stored errors:', errors);
            return errors;
        }
        return [];
    }
};

// Development-only logging and monitoring
if (import.meta.env.DEV) {
    // Global error handlers - DEV only
    window.addEventListener('error', (event) => {
        ErrorLogger.logError('GLOBAL_ERROR', event.error || event.message, {
            filename: event.filename,
            lineno: event.lineno,
            colno: event.colno
        });
    });

    window.addEventListener('unhandledrejection', (event) => {
        ErrorLogger.logError('UNHANDLED_PROMISE', event.reason, {
            promise: event.promise
        });
    });

    // Increase stack trace limit for debugging
    if (typeof Error !== 'undefined') {
        (Error as any).stackTraceLimit = 100;
    }

    // Перехват console.error для специальных случаев
    const originalConsoleError = console.error;
    const originalConsoleWarn = console.warn;

    console.error = (...args) => {
        const errorMessage = args.join(' ');
        
        // TDZ ошибки
        if (errorMessage.includes('Cannot access') && errorMessage.includes('before initialization')) {
            ErrorLogger.logError('TDZ_ERROR', errorMessage, {
                type: 'Temporal Dead Zone',
                possibleCause: 'Circular dependency or hoisting issue'
            });
        }
        // Module loading ошибки
        else if (errorMessage.includes('Loading chunk') || errorMessage.includes('Loading CSS chunk')) {
            ErrorLogger.logError('CHUNK_LOAD_ERROR', errorMessage, {
                type: 'Code splitting issue',
                possibleCause: 'Network error or missing chunk file'
            });
        }
        // React Router ошибки
        else if (errorMessage.includes('router') || errorMessage.includes('route')) {
            ErrorLogger.logError('ROUTER_ERROR', errorMessage, {
                type: 'Routing issue',
                possibleCause: 'Invalid route configuration or navigation error'
            });
        }

        return originalConsoleError.apply(console, args);
    };

    // Логирование warnings
    console.warn = (...args) => {
        const warnMessage = args.join(' ');
        
        if (warnMessage.includes('React') || warnMessage.includes('component')) {
            ErrorLogger.logError('REACT_WARNING', warnMessage, {
                type: 'React Development Warning',
                severity: 'warning'
            });
        }

        return originalConsoleWarn.apply(console, args);
    };

    // Система мониторинга развития dashboard
    const DashboardMonitor = {
        testAllRoutes() {
            const routes = ['/', '/users', '/admins', '/nodes', '/services', '/hosts', '/settings'];
            console.log('🧪 Тестирование маршрутов dashboard:');
            
            routes.forEach(route => {
                try {
                    const url = `${window.location.origin}${window.location.pathname}#${route}`;
                    console.log(`✅ Маршрут ${route}: готов для тестирования - ${url}`);
                } catch (error) {
                    ErrorLogger.logError('ROUTE_TEST_ERROR', error, { route });
                }
            });
            
            return routes.map(route => `${window.location.origin}${window.location.pathname}#${route}`);
        },

        checkAppState() {
            const errors = ErrorLogger.getStoredErrors();
            const state = {
                url: window.location.href,
                hash: window.location.hash,
                errors: errors,
                errorCount: errors.length,
                lastError: errors.slice(-1)[0],
                timestamp: new Date().toISOString()
            };
            
            console.group('📊 Dashboard App State');
            console.log('Current URL:', state.url);
            console.log('Route Hash:', state.hash);
            console.log('Total Errors:', state.errorCount);
            if (state.lastError) {
                console.log('Last Error:', state.lastError);
            }
            console.groupEnd();
            
            return state;
        },

        enableRouteMonitoring() {
            let previousHash = window.location.hash;
            let timeoutId: ReturnType<typeof setTimeout> | null = null;
            
            const checkRouteChange = () => {
                const currentHash = window.location.hash;
                if (currentHash !== previousHash) {
                    console.log(`🔄 Route changed: ${previousHash} → ${currentHash}`);
                    previousHash = currentHash;
                    
                    // Очищаем предыдущий timeout если есть
                    if (timeoutId) {
                        clearTimeout(timeoutId);
                    }
                    
                    // Check for errors after route change
                    timeoutId = setTimeout(() => {
                        const errors = ErrorLogger.getStoredErrors();
                        const recentErrors = errors.filter(
                            (error: any) => new Date(error.timestamp).getTime() > Date.now() - 5000
                        );
                        if (recentErrors.length > 0) {
                            console.warn(`⚠️ Found errors after navigation to ${currentHash}:`, recentErrors);
                        }
                        timeoutId = null;
                    }, 1000);
                }
            };
            
            window.addEventListener('hashchange', checkRouteChange);
            const intervalId = setInterval(checkRouteChange, 1000); // дополнительная проверка
            
            console.log('👁️ Route monitoring включен');
            
            // Возвращаем функцию которая очищает ВСЕ ресурсы
            return () => {
                window.removeEventListener('hashchange', checkRouteChange);
                clearInterval(intervalId);
                if (timeoutId) {
                    clearTimeout(timeoutId);
                    timeoutId = null;
                }
            };
        },

        reportIssues() {
            const errors = ErrorLogger.getStoredErrors();
            const issues = {
                tdz_errors: errors.filter((e: any) => e.category === 'TDZ_ERROR'),
                chunk_errors: errors.filter((e: any) => e.category === 'CHUNK_LOAD_ERROR'),
                router_errors: errors.filter((e: any) => e.category === 'ROUTER_ERROR'),
                react_warnings: errors.filter((e: any) => e.category === 'REACT_WARNING')
            };
            
            console.group('📋 Отчет по проблемам');
            Object.entries(issues).forEach(([type, errors]) => {
                if (errors.length > 0) {
                    console.log(`${type}: ${errors.length} проблем`);
                    errors.forEach((error: any) => console.log(`  - ${error.message}`));
                }
            });
            console.groupEnd();
            
            return issues;
        }
    };
    
    // Экспорт в window для доступа из консоли браузера
    (window as any).ErrorLogger = ErrorLogger;
    (window as any).DashboardMonitor = DashboardMonitor;
    
    console.log('🔧 Development Tools активированы. Доступные команды:');
    console.log('  ErrorLogger.printStoredErrors() - показать все ошибки');
    console.log('  ErrorLogger.clearStoredErrors() - очистить ошибки');
    console.log('  DashboardMonitor.testAllRoutes() - показать все маршруты для тестирования');
    console.log('  DashboardMonitor.checkAppState() - проверить состояние приложения');
    console.log('  DashboardMonitor.enableRouteMonitoring() - включить мониторинг навигации');
    console.log('  DashboardMonitor.reportIssues() - отчет по категориям проблем');
    
    // Автоматически включить мониторинг маршрутов с правильной очисткой
    const cleanupRouteMonitoring = DashboardMonitor.enableRouteMonitoring();
    
    // Обеспечить очистку ресурсов при выгрузке страницы
    const handlePageUnload = () => {
        if (cleanupRouteMonitoring) {
            cleanupRouteMonitoring();
        }
    };
    
    // Зарегистрировать обработчик выгрузки страницы только если window доступен
    if (typeof window !== 'undefined') {
        window.addEventListener('beforeunload', handlePageUnload);
        // Также сохранить функцию очистки в window для ручного вызова если нужно
        (window as any).cleanupRouteMonitoring = cleanupRouteMonitoring;
    }
}

const hashHistory = createHashHistory()

const router = createRouter({ routeTree, history: hashHistory })

declare module '@tanstack/react-router' {
    interface Register {
        router: typeof router
    }
}

// Handle hash routing initialization for direct dashboard access
const initializeHashRouting = async () => {
    // Since dashboard is compiled before install.sh, we need to detect the path at runtime
    // The dashboard is mounted on whatever path was configured in install.sh
    const currentPath = window.location.pathname;
    
    // Check if we're accessing dashboard directly without hash
    // Dashboard could be on /admin/, /dashboard/, or any custom path from install.sh
    const isDirectDashboardAccess = !window.location.hash && (
        currentPath !== '/' && // Not root
        currentPath !== '/login' && // Not direct login
        !currentPath.includes('/api/') && // Not API
        !currentPath.includes('/static/') && // Not static assets
        !currentPath.includes('/locales/') // Not locales
    );
    
    if (isDirectDashboardAccess) {
        console.log(`🔍 Direct dashboard access detected: ${currentPath}`);
        console.log(`🌐 Full URL: ${window.location.href}`);
        
        // Check authentication and redirect accordingly
        try {
            const { useAuth } = await import('@wildosvpn/modules/auth');
            const isLoggedIn = await useAuth.getState().isLoggedIn();
            
            if (isLoggedIn) {
                console.log('🔄 User authenticated, redirecting to dashboard');
                window.location.hash = '#/';
            } else {
                console.log('🔄 User not authenticated, redirecting to login');
                window.location.hash = '#/login';
            }
        } catch (error) {
            console.error('🔄 Auth check failed, redirecting to login:', error);
            window.location.hash = '#/login';
        }
    }
};

// Safe element retrieval with fallback creation
const getRootElement = (): HTMLElement => {
    let rootElement = document.getElementById('app');
    
    if (!rootElement) {
        console.warn('⚠️ Element with id "app" not found, creating fallback element');
        
        // Create the app element as a fallback
        rootElement = document.createElement('div');
        rootElement.id = 'app';
        rootElement.style.cssText = 'width: 100%; height: 100vh; margin: 0; padding: 0;';
        
        // Try to find a suitable parent element
        const body = document.body;
        if (body) {
            // Clear body content if it seems to be a basic HTML page
            if (body.children.length === 0 || (body.children.length === 1 && body.querySelector('script'))) {
                body.innerHTML = '';
            }
            body.appendChild(rootElement);
            console.log('✅ Created and appended app element to body');
        } else {
            // Fallback: wait for DOM and try again
            throw new Error('Document body not available - DOM may not be ready');
        }
    }
    
    return rootElement;
};

// Initialize app with proper error handling
const initializeApp = () => {
    try {
        const rootElement = getRootElement();
        
        // Only render if the element is empty or hasn't been rendered yet
        if (!rootElement.innerHTML || !rootElement.hasChildNodes()) {
            const renderApp = async () => {
                try {
                    console.log('🚀 Starting app initialization...');
                    
                    // Step 1: Initialize core i18n first (backend, plugins, language detection)
                    console.log('📥 Importing i18n config...');
                    const { initializeI18nCore, setupLanguageHandler } = await import('@wildosvpn/features/i18n/config');
                    
                    console.log('🌐 Initializing i18n core...');
                    await initializeI18nCore();
                    
                    console.log('🔗 Setting up language handler...');
                    setupLanguageHandler();
                    
                    // Step 2: Initialize React i18n integration
                    console.log('📥 Importing React i18n bootstrap...');
                    const { initializeReactI18n } = await import('@wildosvpn/features/i18n/bootstrap');
                    
                    console.log('⚛️ Initializing React i18n...');
                    await initializeReactI18n();
                    
                    // Step 3: Create React root
                    console.log('🎯 Creating React root...');
                    const root = ReactDOM.createRoot(rootElement);
                    
                    // Step 4: Render app
                    console.log('🎨 Rendering React app...');
                    root.render(
                        <React.StrictMode>
                            <ErrorBoundary 
                                onError={(error, errorInfo) => {
                                    ErrorLogger.logError('REACT_ERROR_BOUNDARY', error, {
                                        errorInfo,
                                        type: 'React component error'
                                    });
                                }}
                                showToast={true}
                                resetOnPropsChange={true}
                            >
                                <RouterProvider router={router} />
                            </ErrorBoundary>
                        </React.StrictMode>,
                    );
                    console.log('✅ React app mounted successfully');
                } catch (error) {
                    ErrorLogger.logError('REACT_MOUNT_ERROR', error, {
                        type: 'Failed to mount React application'
                    });
                    
                    // Fallback: show error message in the DOM
                    rootElement.innerHTML = `
                        <div style="padding: 20px; text-align: center; font-family: Arial, sans-serif;">
                            <h1 style="color: #dc3545;">Application Failed to Load</h1>
                            <p>There was an error mounting the React application.</p>
                            <p>Please check the browser console for more details.</p>
                            <button onclick="window.location.reload()" style="padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer;">
                                Reload Page
                            </button>
                        </div>
                    `;
                }
            };
            
            // Initialize hash routing BEFORE mounting React router
            initializeHashRouting().then(() => {
                console.log('✅ Hash routing initialized successfully');
            }).catch((error) => {
                ErrorLogger.logError('INITIALIZATION_ERROR', error, {
                    type: 'Hash routing initialization failed'
                });
                console.warn('⚠️ Hash routing failed, proceeding with app render');
            });
            renderApp().catch(err => 
                ErrorLogger.logError('APP_INIT_ERROR', err, {
                    type: 'Failed to initialize application'
                })
            );
        } else {
            console.log('🔄 App element already has content, skipping render');
        }
    } catch (error) {
        ErrorLogger.logError('APP_INITIALIZATION_ERROR', error, {
            type: 'Critical app initialization failure'
        });
        
        // Last resort: try to show an error message using safe DOM manipulation
        try {
            // Clear body content safely
            document.body.innerHTML = '';
            
            // Create elements safely without innerHTML injection
            const container = document.createElement('div');
            container.style.cssText = 'padding: 20px; text-align: center; font-family: Arial, sans-serif; background: #f8f9fa; min-height: 100vh; display: flex; align-items: center; justify-content: center;';
            
            const innerDiv = document.createElement('div');
            innerDiv.style.cssText = 'max-width: 500px;';
            
            const title = document.createElement('h1');
            title.style.color = '#dc3545';
            title.textContent = 'Critical Error';
            
            const description = document.createElement('p');
            description.textContent = 'The application failed to initialize properly.';
            
            const errorMsg = document.createElement('p');
            errorMsg.textContent = `Error: ${error instanceof Error ? error.message : 'Unknown error'}`;
            
            const reloadButton = document.createElement('button');
            reloadButton.style.cssText = 'padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; margin-top: 10px;';
            reloadButton.textContent = 'Reload Page';
            reloadButton.addEventListener('click', () => window.location.reload());
            
            innerDiv.appendChild(title);
            innerDiv.appendChild(description);
            innerDiv.appendChild(errorMsg);
            innerDiv.appendChild(reloadButton);
            container.appendChild(innerDiv);
            document.body.appendChild(container);
        } catch (fallbackError) {
            console.error('❌ Even fallback error display failed:', fallbackError);
        }
    }
};

// Wait for DOM to be ready before initializing
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeApp);
} else {
    // DOM is already ready
    initializeApp();
}
