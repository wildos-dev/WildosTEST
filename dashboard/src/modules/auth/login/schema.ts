import { z } from 'zod';
import { TFunction } from 'i18next';

export const createLoginSchema = (t: TFunction) => z.object({
    username: z.string().nonempty(t('page.login.username.error.is-required')),
    password: z.string().nonempty(t('page.login.password.error.is-required')),
});

// Keep backward compatibility
export const LoginSchema = z.object({
    username: z.string().nonempty('Username is required'),
    password: z.string().nonempty('Password is required'),
});
