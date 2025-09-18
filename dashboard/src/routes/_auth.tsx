import { Outlet, createFileRoute } from '@tanstack/react-router'

const AuthLayout = () => {
  return (
    <div className='w-screen h-screen flex justify-center items-center bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900'>
      <div className="w-full h-full">
        <Outlet />
      </div>
    </div>
  )
}

export const Route = createFileRoute('/_auth')({
  component: () => <AuthLayout />,
})
