import { Card, CardContent, CardHeader, CardTitle } from '@wildosvpn/common/components';
import { LoginForm } from '@wildosvpn/modules/auth';
import { createFileRoute } from '@tanstack/react-router'
import * as React from 'react'
import { useTranslation } from 'react-i18next';
import logoImage from '../../assets/logo.png';
import './login.css';

const LoginPage: React.FC = () => {
  const { t } = useTranslation();
  return (
    <div className='flex flex-col justify-center items-center p-4 w-full h-full min-h-screen'>
      {/* Animated background pattern */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-blue-500/10 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-green-500/10 rounded-full blur-3xl animate-pulse animation-delay-2000"></div>
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-orange-500/5 rounded-full blur-3xl animate-pulse animation-delay-4000"></div>
      </div>
      
      {/* Logo Section */}
      <div className="mb-8 text-center relative z-10">
        <div className="mb-6 relative">
          <img 
            src={logoImage} 
            alt={t('logo.wildos-vpn')} 
            className="h-40 w-auto mx-auto drop-shadow-2xl filter brightness-110"
          />
        </div>
      </div>
      
      {/* Login Card */}
      <Card className="p-8 w-full max-w-md shadow-2xl border border-slate-700/50 bg-slate-800/90 backdrop-blur-xl relative z-10">
        <div className="absolute inset-0 bg-gradient-to-r from-blue-500/5 to-emerald-500/5 rounded-lg"></div>
        <CardHeader className="text-center pb-6 relative">
          <CardTitle className="font-header text-2xl text-white">
            {t('login')}
          </CardTitle>
        </CardHeader>
        <CardContent className="relative">
          <LoginForm />
        </CardContent>
      </Card>
      
      {/* Footer */}
      <div className="mt-8 text-center text-sm text-slate-400 relative z-10">
        <p>{t('copyright.text')}</p>
      </div>
    </div>
  );
};

export const Route = createFileRoute('/_auth/login')({
  component: () => <LoginPage />
})
