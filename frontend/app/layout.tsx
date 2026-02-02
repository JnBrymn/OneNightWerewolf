export const metadata = {
  title: 'One Night Werewolf',
  description: 'A fast-paced game of deduction and deception',
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

