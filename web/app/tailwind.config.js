/** @type {import('tailwindcss').Config} */
export default {
    darkMode: ['selector', 'html.dark'],
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                border: "hsl(var(--border))",
                input: "hsl(var(--input))",
                ring: "hsl(var(--ring))",
                background: "hsl(var(--background))",
                foreground: "hsl(var(--foreground))",
                primary: {
                    DEFAULT: "hsl(var(--primary))",
                    foreground: "hsl(var(--primary-foreground))",
                },
                secondary: {
                    DEFAULT: "hsl(var(--secondary))",
                    foreground: "hsl(var(--secondary-foreground))",
                },
                destructive: {
                    DEFAULT: "hsl(var(--destructive))",
                    foreground: "hsl(var(--destructive-foreground))",
                },
                muted: {
                    DEFAULT: "hsl(var(--muted))",
                    foreground: "hsl(var(--muted-foreground))",
                },
                accent: {
                    DEFAULT: "hsl(var(--accent))",
                    foreground: "hsl(var(--accent-foreground))",
                },
                popover: {
                    DEFAULT: "hsl(var(--popover))",
                    foreground: "hsl(var(--popover-foreground))",
                },
                card: {
                    DEFAULT: "hsl(var(--card))",
                    foreground: "hsl(var(--card-foreground))",
                },
            },
            borderRadius: {
                sm: "calc(var(--radius) - 0.25rem)",
                DEFAULT: "var(--radius)",
                md: "var(--radius)",
                lg: "calc(var(--radius) * 1.33)",
                xl: "calc(var(--radius) * 1.5)",
                "2xl": "calc(var(--radius) * 2)",
                "3xl": "calc(var(--radius) * 2.67)",
                "4xl": "calc(var(--radius) * 4)",
            },
            fontFamily: {
                sans: ['Inter', 'system-ui', 'sans-serif'],
                inter: ['Inter', 'system-ui', 'sans-serif'],
                display: ['"Plus Jakarta Sans"', 'Inter', 'system-ui', 'sans-serif'],
            },
            boxShadow: {
                card: 'var(--card-shadow)',
                'card-hover': 'var(--card-shadow-hover)',
            },
        },
    },
    plugins: [],
}
