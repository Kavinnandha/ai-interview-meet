import '../styles/globals.css';
import '@livekit/components-styles';
import '@livekit/components-styles/prefabs';
import type { Metadata, Viewport } from 'next';
import { Toaster } from 'react-hot-toast';

export const metadata: Metadata = {
  title: {
    default: 'Sri Shakthi Meet | Video Conferencing Platform',
    template: '%s',
  },
  description:
    'Sri Shakthi Meet is a video conferencing platform built with LiveKit technology, providing scalable and real-time audio and video communication for education and collaboration.',
  twitter: {
    creator: '@srishakthi',
    site: '@srishakthi',
    card: 'summary_large_image',
  },
  openGraph: {
    url: 'https://meet.srishakthi.edu',
    images: [
      {
        url: 'https://meet.srishakthi.edu/images/sri-shakthi-logo.png',
        width: 830,
        height: 143,
        type: 'image/png',
      },
    ],
    siteName: 'Sri Shakthi Meet',
  },
  icons: {
    icon: {
      rel: 'icon',
      url: '/favicon.ico',
    },
    apple: [
      {
        rel: 'apple-touch-icon',
        url: '/images/livekit-apple-touch.png',
        sizes: '180x180',
      },
      { rel: 'mask-icon', url: '/images/livekit-safari-pinned-tab.svg', color: '#070707' },
    ],
  },
};

export const viewport: Viewport = {
  themeColor: '#070707',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body data-lk-theme="default">
        <Toaster />
        {children}
      </body>
    </html>
  );
}
