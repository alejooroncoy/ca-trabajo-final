/** @type {import('tailwindcss').Config} */
export default {
	content: ['./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}'],
	theme: {
		extend: {
			backgroundImage: {
				'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
			},
			colors: {
				// Paleta basada en la imagen: azules, coral/naranja, rojos
				'blue-dark': '#1A3A5C',
				'blue-medium': '#2E5C8A',
				'blue-primary': '#4A90E2',
				'blue-light': '#6BA3E8',
				'blue-map': '#5B9BD5', // Azul del mapa
				'coral': '#FF6B6B', // Coral del camión y pins
				'coral-light': '#FF8E53', // Coral claro
				'coral-dark': '#FF7F50', // Coral oscuro
				'red-route': '#EF4444', // Rojo de la ruta punteada
				'red-pin': '#DC2626', // Rojo de los pins
			},
			fontFamily: {
				sans: ['Inter', 'system-ui', 'sans-serif'],
			},
			animation: {
				'truck-move': 'truck-move 8s ease-in-out infinite',
				'packages-float': 'packages-float 6s ease-in-out infinite',
				'pin-bounce': 'pin-bounce 4s ease-in-out infinite',
				'clock-rotate': 'clock-rotate 10s linear infinite',
				'arrow-pulse': 'arrow-pulse 3s ease-in-out infinite',
				'spin-slow': 'spin 20s linear infinite',
			},
			keyframes: {
				'truck-move': {
					'0%, 100%': { transform: 'translateX(0) translateY(0)' },
					'50%': { transform: 'translateX(-20px) translateY(-10px)' },
				},
				'packages-float': {
					'0%, 100%': { transform: 'translateY(0) rotate(0deg)' },
					'50%': { transform: 'translateY(-15px) rotate(2deg)' },
				},
				'pin-bounce': {
					'0%, 100%': { transform: 'translateY(0) scale(1)' },
					'50%': { transform: 'translateY(-10px) scale(1.05)' },
				},
				'clock-rotate': {
					'0%': { transform: 'rotate(0deg)' },
					'100%': { transform: 'rotate(360deg)' },
				},
				'arrow-pulse': {
					'0%, 100%': { opacity: '0.4', transform: 'translate(-50%, -50%) scale(1)' },
					'50%': { opacity: '0.6', transform: 'translate(-50%, -50%) scale(1.1)' },
				},
			},
		},
	},
	plugins: [],
};

