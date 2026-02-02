export const metadata = {
  title: 'Ping Application',
  description: 'Simple Next.js and FastAPI demo',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}

