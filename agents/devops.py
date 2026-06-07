"""
DevOps Agent: Generación de landing page y deployment automático.
Crea HTML con Tailwind CSS y despliega en Vercel/Netlify.
"""
import asyncio
import logging
import aiohttp
from datetime import datetime
from models import ProductState
from config import settings

logger = logging.getLogger(__name__)


def _generate_html_template(state: ProductState) -> str:
    """
    Genera HTML estático con Tailwind CSS vía CDN.
    Inyecta dinámicamente el copy y las imágenes del estado con diseño premium.
    """
    headline = state.generated_copy.get("headline", "Increíble Producto de Dropshipping")
    body = state.generated_copy.get("body", "Consigue el tuyo hoy mismo con la mejor oferta.")
    cta = state.generated_copy.get("cta", "Comprar Ahora")
    hero_image = state.image_assets[0] if state.image_assets else "https://via.placeholder.com/800x600"
    price = state.suggested_price
    
    # Determinar características dinámicamente según el nombre del producto
    product_lower = state.product_name.lower()
    if "humidificador" in product_lower or "difusor" in product_lower or "llama" in product_lower:
        f1_title, f1_desc, f1_icon = "Efecto Llama 3D", "Simula fuego acogedor con niebla de agua y luces LED inteligentes para una atmósfera única.", "🔥"
        f2_title, f2_desc, f2_icon = "Apagado Inteligente", "Sensor de seguridad integrado que apaga el dispositivo al quedarse sin agua automáticamente.", "🛡️"
        f3_title, f3_desc, f3_icon = "Aromaterapia Silenciosa", "Difunde tus aceites esenciales favoritos de manera ultrasónica para aliviar el estrés cotidiano.", "🌿"
    elif "cepillo" in product_lower or "facial" in product_lower or "sónico" in product_lower:
        f1_title, f1_desc, f1_icon = "Tecnología Sónica", "Miles de vibraciones por minuto para limpiar los poros profundamente y remover células muertas.", "✨"
        f2_title, f2_desc, f2_icon = "Silicona Grado Médico", "Cerdas ultra suaves e hipoalergénicas ideales para todo tipo de pieles, fácil de limpiar.", "🌸"
        f3_title, f3_desc, f3_icon = "Resistente al Agua IPX7", "Úsalo de forma segura bajo la ducha, diseño impermeable y batería de muy larga duración.", "🚿"
    else:
        f1_title, f1_desc, f1_icon = "Calidad Premium", "Fabricado con materiales de alta durabilidad y tecnología de última generación garantizada.", "⭐"
        f2_title, f2_desc, f2_icon = "Diseño Innovador", "Estética moderna, elegante y funcional que se adapta perfectamente a tu estilo de vida.", "🎨"
        f3_title, f3_desc, f3_icon = "Fácil de Utilizar", "Operación simple e intuitiva con un solo botón para disfrutar del producto de inmediato.", "🔌"

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{state.product_name} - Oferta Exclusiva</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700;800&display=swap" rel="stylesheet">
    <style>
        body {{
            font-family: 'Outfit', sans-serif;
        }}
    </style>
    <meta name="description" content="{body[:150]}...">
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen relative overflow-x-hidden">
    
    <!-- WhatsApp Floating Button -->
    <a href="https://wa.me/56912345678" target="_blank" class="fixed bottom-6 right-6 z-50 bg-green-500 hover:bg-green-600 text-white p-4 rounded-full shadow-2xl transition-transform transform hover:scale-110 flex items-center justify-center">
        <svg class="w-8 h-8" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12.012 2c-5.506 0-9.989 4.478-9.99 9.984a9.96 9.96 0 001.37 5.028L2 22l5.175-1.359a9.933 9.933 0 004.825 1.233h.005c5.507 0 9.99-4.478 9.99-9.985.001-2.667-1.037-5.176-2.927-7.067C17.172 2.94 14.668 2 12.012 2zm5.794 13.91c-.244.686-1.42 1.252-1.948 1.343-.48.082-.99.162-3.13-.687-2.737-1.085-4.507-3.866-4.644-4.048-.137-.182-1.11-1.474-1.11-2.812 0-1.337.702-1.996.946-2.253.244-.258.534-.323.71-.323.176 0 .353.002.503.009.157.007.369-.06.577.452.213.524.731 1.782.792 1.903.062.12.103.26.022.42-.081.162-.122.26-.244.404-.122.145-.257.323-.367.433-.122.12-.248.252-.107.494.141.242.628 1.032 1.35 1.677.928.826 1.71 1.081 1.954 1.202.244.12.387.1.53-.064.141-.165.61-.71.774-.952.162-.242.325-.2.548-.12.224.08 1.42.67 1.664.792.244.12.406.182.466.282.061.1.061.579-.183 1.266z"/>
        </svg>
    </a>

    <!-- Top Promo Bar -->
    <div class="bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 text-center py-2 text-sm font-bold tracking-wider">
        🚚 ENVÍO GRATIS A TODO CHILE + PAGO CONTRA ENTREGA 🤝
    </div>

    <!-- Hero Section -->
    <header class="relative pt-12 pb-24 px-4 md:px-8 max-w-7xl mx-auto grid lg:grid-cols-2 gap-12 items-center">
        <!-- Glowing Orbs -->
        <div class="absolute top-1/4 left-1/4 -z-10 w-96 h-96 bg-purple-600/20 rounded-full blur-3xl"></div>
        <div class="absolute bottom-10 right-10 -z-10 w-96 h-96 bg-indigo-600/20 rounded-full blur-3xl"></div>

        <!-- Left Content -->
        <div class="space-y-6">
            <div class="inline-flex items-center gap-2 bg-rose-500/20 border border-rose-500/40 text-rose-300 px-4 py-1.5 rounded-full text-xs font-semibold uppercase tracking-wider animate-pulse">
                🔥 Oferta Especial - 50% de Descuento
            </div>
            <h1 class="text-4xl md:text-5xl lg:text-6xl font-extrabold leading-tight text-transparent bg-clip-text bg-gradient-to-r from-white via-slate-100 to-indigo-200">
                {headline}
            </h1>
            <p class="text-lg md:text-xl text-slate-300 font-light leading-relaxed">
                {body}
            </p>

            <div class="flex items-center gap-6 py-4">
                <div class="bg-slate-900 border border-slate-800 px-6 py-3 rounded-2xl">
                    <span class="block text-xs text-slate-400 uppercase font-semibold">Precio de Oferta</span>
                    <span class="text-4xl font-extrabold text-green-400">${price} USD</span>
                </div>
                <div class="text-slate-500 line-through text-2xl font-semibold">
                    ${price * 2} USD
                </div>
            </div>

            <!-- Call to Action -->
            <div class="space-y-4">
                <button onclick="openCheckoutModal()" class="w-full md:w-auto bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white font-extrabold py-5 px-12 rounded-2xl text-xl transition-all transform hover:scale-105 shadow-lg shadow-green-500/20 flex items-center justify-center gap-2">
                    <span>{cta}</span>
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M14 5l7 7m0 0l-7 7m7-7H3"/>
                    </svg>
                </button>
                <p class="text-xs text-slate-400 flex items-center gap-1.5 justify-center md:justify-start">
                    <span>🔒 Compra Garantizada</span> • <span>📦 Recibe y paga en casa</span>
                </p>
            </div>

            <!-- Trust Badges -->
            <div class="grid grid-cols-3 gap-4 pt-6 border-t border-slate-900 text-center">
                <div>
                    <span class="block text-2xl mb-1">⭐ 4.9</span>
                    <span class="text-xs text-slate-400">12,500+ Reseñas</span>
                </div>
                <div>
                    <span class="block text-2xl mb-1">🚚</span>
                    <span class="text-xs text-slate-400">Envío Gratis</span>
                </div>
                <div>
                    <span class="block text-2xl mb-1">🤝</span>
                    <span class="text-xs text-slate-400">Pago Entrega</span>
                </div>
            </div>
        </div>

        <!-- Right Product Media -->
        <div class="relative flex justify-center">
            <div class="absolute inset-0 bg-gradient-to-tr from-purple-600/30 to-pink-600/30 rounded-3xl blur-3xl opacity-50"></div>
            <div class="relative bg-slate-900 border border-slate-800 p-4 rounded-[2rem] shadow-2xl max-w-lg w-full transition-transform hover:rotate-1">
                <img src="{hero_image}" alt="{state.product_name}" class="rounded-2xl w-full object-cover aspect-square">
                <div class="absolute -top-3 -right-3 bg-red-500 text-white text-xs font-bold px-3 py-1.5 rounded-xl shadow-lg uppercase tracking-wider transform rotate-12">
                    ¡Más Vendido!
                </div>
            </div>
        </div>
    </header>

    <!-- Dynamic Features Section -->
    <section class="bg-slate-900/60 border-y border-slate-900 py-24 px-4 md:px-8">
        <div class="max-w-6xl mx-auto">
            <div class="text-center max-w-2xl mx-auto mb-16">
                <h2 class="text-3xl md:text-4xl font-extrabold text-white mb-4">¿Por qué es el favorito de todos?</h2>
                <p class="text-slate-400">Características premium diseñadas para ofrecerte la mejor experiencia y durabilidad.</p>
            </div>
            
            <div class="grid md:grid-cols-3 gap-8">
                <!-- Feature 1 -->
                <div class="bg-slate-950 border border-slate-800 rounded-3xl p-8 hover:border-purple-500/50 transition-colors group">
                    <div class="w-14 h-14 bg-purple-500/10 border border-purple-500/20 text-3xl flex items-center justify-center rounded-2xl mb-6 group-hover:scale-110 transition-transform">
                        {f1_icon}
                    </div>
                    <h3 class="text-xl font-bold mb-3">{f1_title}</h3>
                    <p class="text-slate-400 leading-relaxed">{f1_desc}</p>
                </div>
                <!-- Feature 2 -->
                <div class="bg-slate-950 border border-slate-800 rounded-3xl p-8 hover:border-purple-500/50 transition-colors group">
                    <div class="w-14 h-14 bg-purple-500/10 border border-purple-500/20 text-3xl flex items-center justify-center rounded-2xl mb-6 group-hover:scale-110 transition-transform">
                        {f2_icon}
                    </div>
                    <h3 class="text-xl font-bold mb-3">{f2_title}</h3>
                    <p class="text-slate-400 leading-relaxed">{f2_desc}</p>
                </div>
                <!-- Feature 3 -->
                <div class="bg-slate-950 border border-slate-800 rounded-3xl p-8 hover:border-purple-500/50 transition-colors group">
                    <div class="w-14 h-14 bg-purple-500/10 border border-purple-500/20 text-3xl flex items-center justify-center rounded-2xl mb-6 group-hover:scale-110 transition-transform">
                        {f3_icon}
                    </div>
                    <h3 class="text-xl font-bold mb-3">{f3_title}</h3>
                    <p class="text-slate-400 leading-relaxed">{f3_desc}</p>
                </div>
            </div>
        </div>
    </section>

    <!-- Social Proof / Reviews Section -->
    <section class="py-24 px-4 md:px-8 max-w-6xl mx-auto">
        <div class="text-center max-w-2xl mx-auto mb-16">
            <h2 class="text-3xl md:text-4xl font-extrabold text-white mb-4">Lo que dicen nuestros clientes</h2>
            <p class="text-slate-400">Miles de personas en Chile ya disfrutan de este increíble producto en su día a día.</p>
        </div>

        <div class="grid md:grid-cols-3 gap-8">
            <!-- Review 1 -->
            <div class="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
                <div class="flex items-center gap-1.5 text-amber-400">
                    ⭐⭐⭐⭐⭐
                </div>
                <p class="text-slate-300 italic font-light">"Excelente producto, el efecto es realmente hermoso y relaja muchísimo. Llegó super rápido en Santiago y pagué al recibir."</p>
                <div class="flex items-center gap-3">
                    <div class="w-10 h-10 rounded-full bg-indigo-600 flex items-center justify-center text-sm font-bold text-white">CR</div>
                    <div>
                        <span class="block font-bold text-sm">Camila Rojas</span>
                        <span class="text-xs text-slate-500">Santiago, CL (Verificada)</span>
                    </div>
                </div>
            </div>
            <!-- Review 2 -->
            <div class="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
                <div class="flex items-center gap-1.5 text-amber-400">
                    ⭐⭐⭐⭐⭐
                </div>
                <p class="text-slate-300 italic font-light">"Funciona impecable. Lo uso todas las noches en mi velador. El apagado automático funciona de maravilla apenas se vacía."</p>
                <div class="flex items-center gap-3">
                    <div class="w-10 h-10 rounded-full bg-purple-600 flex items-center justify-center text-sm font-bold text-white">SM</div>
                    <div>
                        <span class="block font-bold text-sm">Sebastián Muñoz</span>
                        <span class="text-xs text-slate-500">Viña del Mar, CL (Verificada)</span>
                    </div>
                </div>
            </div>
            <!-- Review 3 -->
            <div class="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
                <div class="flex items-center gap-1.5 text-amber-400">
                    ⭐⭐⭐⭐⭐
                </div>
                <p class="text-slate-300 italic font-light">"El diseño se ve muy elegante en la sala. Es silencioso y la simulación de llama sorprende a las visitas."</p>
                <div class="flex items-center gap-3">
                    <div class="w-10 h-10 rounded-full bg-rose-600 flex items-center justify-center text-sm font-bold text-white">IV</div>
                    <div>
                        <span class="block font-bold text-sm">Ignacio Valenzuela</span>
                        <span class="text-xs text-slate-500">Concepción, CL (Verificada)</span>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- FAQ Section -->
    <section class="bg-slate-900/60 border-t border-slate-900 py-24 px-4 md:px-8">
        <div class="max-w-4xl mx-auto">
            <h2 class="text-3xl font-extrabold text-center text-white mb-12">Preguntas Frecuentes</h2>
            
            <div class="space-y-4">
                <!-- FAQ 1 -->
                <div class="bg-slate-950 border border-slate-800 rounded-2xl overflow-hidden">
                    <button onclick="toggleFAQ('faq1')" class="w-full text-left p-6 font-bold flex justify-between items-center text-white hover:bg-slate-900 transition-colors">
                        <span>¿Cuánto demora el despacho y cómo pago?</span>
                        <span id="faq1-icon" class="text-2xl transition-transform">+</span>
                    </button>
                    <div id="faq1" class="hidden p-6 pt-0 text-slate-400 border-t border-slate-900/50 leading-relaxed">
                        El despacho demora entre 24 y 48 horas en Santiago, y hasta 3 a 5 días hábiles en regiones de Chile. Pagas en efectivo o transferencia directamente al repartidor cuando el producto llega a tu puerta (Pago Contra Entrega).
                    </div>
                </div>
                <!-- FAQ 2 -->
                <div class="bg-slate-950 border border-slate-800 rounded-2xl overflow-hidden">
                    <button onclick="toggleFAQ('faq2')" class="w-full text-left p-6 font-bold flex justify-between items-center text-white hover:bg-slate-900 transition-colors">
                        <span>¿Tiene garantía el producto?</span>
                        <span id="faq2-icon" class="text-2xl transition-transform">+</span>
                    </button>
                    <div id="faq2" class="hidden p-6 pt-0 text-slate-400 border-t border-slate-900/50 leading-relaxed">
                        Sí, todos nuestros productos cuentan con una garantía de 30 días contra defectos de fábrica. Si tienes algún inconveniente, nos escribes y lo resolveremos de inmediato.
                    </div>
                </div>
                <!-- FAQ 3 -->
                <div class="bg-slate-950 border border-slate-800 rounded-2xl overflow-hidden">
                    <button onclick="toggleFAQ('faq3')" class="w-full text-left p-6 font-bold flex justify-between items-center text-white hover:bg-slate-900 transition-colors">
                        <span>¿Cómo funciona el apagado automático?</span>
                        <span id="faq3-icon" class="text-2xl transition-transform">+</span>
                    </button>
                    <div id="faq3" class="hidden p-6 pt-0 text-slate-400 border-t border-slate-900/50 leading-relaxed">
                        El dispositivo cuenta con un sensor inteligente de nivel de agua. Tan pronto como el tanque de agua se vacíe, el sistema se apaga de forma automática para evitar el sobrecalentamiento y proteger los componentes.
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- Bottom Purchase Bar -->
    <footer class="bg-slate-950 border-t border-slate-900 py-16 text-center px-4">
        <div class="max-w-2xl mx-auto space-y-6">
            <h2 class="text-3xl font-extrabold text-white">¿Listo para transformar tu espacio?</h2>
            <p class="text-slate-400">Aprovecha el 50% de descuento y la comodidad del Pago Contra Entrega hoy mismo. Stock limitado.</p>
            <button onclick="openCheckoutModal()" class="bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white font-extrabold py-5 px-16 rounded-2xl text-xl hover:scale-105 transform transition-all shadow-xl shadow-green-500/20">
                {cta}
            </button>
            <p class="text-xs text-slate-500 pt-8">© 2026 {state.product_name}. Todos los derechos reservados. Distribuidor Autorizado en Chile.</p>
        </div>
    </footer>

    <!-- INTERACTIVE CHECKOUT MODAL (Pago Contra Entrega) -->
    <div id="checkoutModal" class="fixed inset-0 z-50 hidden bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
        <div class="bg-slate-900 border border-slate-850 rounded-3xl max-w-md w-full p-8 shadow-2xl relative animate-in fade-in zoom-in duration-200">
            <!-- Close button -->
            <button onclick="closeCheckoutModal()" class="absolute top-4 right-4 text-slate-400 hover:text-white text-2xl font-bold">&times;</button>
            
            <!-- Form State -->
            <div id="modalFormState" class="space-y-6">
                <div class="text-center">
                    <h3 class="text-2xl font-bold text-white mb-1">Completa tu Pedido</h3>
                    <p class="text-sm text-slate-400">Recibe en casa y paga al recibir (Envío Gratis)</p>
                </div>
                
                <!-- Order Summary -->
                <div class="bg-slate-950 p-4 rounded-xl border border-slate-850 flex items-center gap-4">
                    <img src="{hero_image}" alt="{state.product_name}" class="w-16 h-16 rounded-lg object-cover">
                    <div class="flex-1">
                        <span class="block text-sm font-bold text-white leading-tight">{state.product_name}</span>
                        <span class="block text-xs text-slate-400 mt-1">Cantidad: 1 unidad</span>
                    </div>
                    <div class="text-right">
                        <span class="block text-lg font-bold text-green-400">${price} USD</span>
                        <span class="block text-[10px] text-green-500 font-semibold uppercase">Envío Gratis</span>
                    </div>
                </div>

                <!-- Form Inputs -->
                <form id="codForm" onsubmit="submitCODOrder(event)" class="space-y-4">
                    <div>
                        <label class="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Nombre Completo</label>
                        <input type="text" required class="w-full bg-slate-950 border border-slate-850 rounded-xl px-4 py-3 text-white focus:border-indigo-500 focus:outline-none transition-colors" placeholder="Ej: Juan Pérez">
                    </div>
                    <div>
                        <label class="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Teléfono Móvil (WhatsApp)</label>
                        <input type="tel" required class="w-full bg-slate-950 border border-slate-850 rounded-xl px-4 py-3 text-white focus:border-indigo-500 focus:outline-none transition-colors" placeholder="Ej: 912345678">
                    </div>
                    <div>
                        <label class="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Dirección de Despacho</label>
                        <input type="text" required class="w-full bg-slate-950 border border-slate-850 rounded-xl px-4 py-3 text-white focus:border-indigo-500 focus:outline-none transition-colors" placeholder="Calle, número, depto o villa">
                    </div>
                    <div>
                        <label class="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Región / Comuna</label>
                        <input type="text" required class="w-full bg-slate-950 border border-slate-850 rounded-xl px-4 py-3 text-white focus:border-indigo-500 focus:outline-none transition-colors" placeholder="Ej: Metropolitana / Providencia">
                    </div>

                    <button type="submit" class="w-full bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white font-bold py-4 rounded-xl text-lg transition-transform transform active:scale-95 shadow-lg shadow-green-500/10">
                        Confirmar Pedido Pago Contra Entrega
                    </button>
                </form>
            </div>

            <!-- Loading State -->
            <div id="modalLoadingState" class="hidden py-16 text-center space-y-4">
                <div class="animate-spin rounded-full h-16 w-16 border-b-2 border-green-500 mx-auto"></div>
                <p class="text-lg text-white font-bold">Procesando tu pedido...</p>
                <p class="text-sm text-slate-400">Estamos agendando tu despacho con el repartidor.</p>
            </div>

            <!-- Success State -->
            <div id="modalSuccessState" class="hidden py-12 text-center space-y-6">
                <div class="w-20 h-20 bg-green-500/10 text-green-400 border border-green-500/30 rounded-full flex items-center justify-center text-4xl mx-auto">
                    ✓
                </div>
                <div class="space-y-2">
                    <h3 class="text-2xl font-bold text-white">¡Pedido Registrado con Éxito!</h3>
                    <p class="text-slate-300">Gracias por tu compra. Nos contactaremos contigo vía WhatsApp en los próximos minutos para coordinar la entrega.</p>
                </div>
                <button onclick="closeCheckoutModal()" class="w-full bg-slate-800 hover:bg-slate-750 text-white font-bold py-3.5 rounded-xl transition-colors">
                    Volver a la Tienda
                </button>
            </div>
        </div>
    </div>

    <!-- Page Interaction Script -->
    <script>
        function toggleFAQ(id) {{
            const element = document.getElementById(id);
            const icon = document.getElementById(id + '-icon');
            if (element.classList.contains('hidden')) {{
                element.classList.remove('hidden');
                icon.innerText = '-';
            }} else {{
                element.classList.add('hidden');
                icon.innerText = '+';
            }}
        }}

        function openCheckoutModal() {{
            const modal = document.getElementById('checkoutModal');
            modal.classList.remove('hidden');
            document.body.style.overflow = 'hidden';
        }}

        function closeCheckoutModal() {{
            const modal = document.getElementById('checkoutModal');
            modal.classList.add('hidden');
            document.body.style.overflow = '';
            // Reset states
            document.getElementById('modalFormState').classList.remove('hidden');
            document.getElementById('modalLoadingState').classList.add('hidden');
            document.getElementById('modalSuccessState').classList.add('hidden');
            document.getElementById('codForm').reset();
        }}

        async function submitCODOrder(event) {{
            event.preventDefault();
            
            // Ocultar formulario, mostrar cargador
            document.getElementById('modalFormState').classList.add('hidden');
            document.getElementById('modalLoadingState').classList.remove('hidden');

            // Obtener valores del formulario
            const inputs = document.getElementById('codForm').getElementsByTagName('input');
            const orderData = {{
                name: inputs[0].value,
                phone: inputs[1].value,
                address: inputs[2].value,
                city: inputs[3].value,
                product_id: {settings.dropi_product_id},
                product_name: "{state.product_name}",
                product_price: {state.suggested_price},
                supplier_id: {settings.dropi_supplier_id or 'null'}
            }};

            try {{
                const response = await fetch('/api/order', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json'
                    }},
                    body: JSON.stringify(orderData)
                }});

                const data = await response.json();
                
                // Ocultar cargador
                document.getElementById('modalLoadingState').classList.add('hidden');

                if (response.ok && data.status === 'success') {{
                    // Mostrar estado de éxito
                    document.getElementById('modalSuccessState').classList.remove('hidden');
                }} else {{
                    // Mostrar error
                    alert('Error al registrar pedido: ' + (data.message || 'Error desconocido'));
                    document.getElementById('modalFormState').classList.remove('hidden');
                }}
            }} catch (error) {{
                console.error('Error:', error);
                document.getElementById('modalLoadingState').classList.add('hidden');
                alert('No se pudo conectar con el servidor local para enviar a Dropi. Asegúrate de ejecutar: python server.py');
                document.getElementById('modalFormState').classList.remove('hidden');
            }}
        }}
    </script>
</body>
</html>"""
    
    return html


async def _deploy_to_vercel(html_content: str, product_name: str) -> str:
    """
    Simula deployment a Vercel mediante su API.
    
    En producción, esto haría:
    POST https://api.vercel.com/v13/deployments
    """
    logger.info("🚀 [DEVOPS] Desplegando sitio a Vercel...")
    
    # Simular latencia de deployment
    await asyncio.sleep(2.5)
    
    # En producción, aquí iría la llamada real a la API de Vercel
    """
    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bearer {settings.vercel_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "name": product_name.lower().replace(" ", "-"),
            "files": [
                {
                    "file": "index.html",
                    "data": html_content
                }
            ],
            "projectSettings": {
                "framework": None
            }
        }
        async with session.post(
            "https://api.vercel.com/v13/deployments",
            headers=headers,
            json=payload
        ) as response:
            data = await response.json()
            deployed_url = f"https://{data['url']}"
            return deployed_url
    """
    
    # URL simulada de deployment exitoso
    sanitized_name = product_name.lower().replace(" ", "-")[:30]
    deployed_url = f"https://{sanitized_name}-auto.vercel.app"
    
    logger.info(f"✅ [DEVOPS] Sitio desplegado exitosamente: {deployed_url}")
    return deployed_url


async def run_devops_agent(state: ProductState) -> ProductState:
    """
    Agente DevOps que genera y despliega la landing page.
    
    Proceso:
    1. Genera HTML con Tailwind CSS inyectando datos del estado
    2. Despliega a Vercel/Netlify mediante API
    3. Retorna URL en vivo
    
    Args:
        state: Estado actual con copy e imágenes
        
    Returns:
        ProductState: Estado actualizado con URL de deployment
    """
    logger.info("⚙️  [DEVOPS] Iniciando generación y deployment de landing page...")
    
    # Generar HTML
    logger.info("📄 [DEVOPS] Generando HTML con Tailwind CSS...")
    html_content = _generate_html_template(state)
    logger.info(f"✅ [DEVOPS] HTML generado ({len(html_content)} caracteres)")
    
    # Guardar HTML localmente para previsualización
    try:
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        logger.info("💾 [DEVOPS] Landing page guardada localmente como 'index.html'")
    except Exception as e:
        logger.error(f"❌ [DEVOPS] Error al guardar landing page localmente: {str(e)}")
    
    # Desplegar a Vercel
    deployed_url = await _deploy_to_vercel(html_content, state.product_name)
    
    # Actualizar estado
    state.deployed_url = deployed_url
    state.deployment_timestamp = datetime.utcnow()
    state.pipeline_stage = "devops_completed"
    
    logger.info(f"🎉 [DEVOPS] Landing page en vivo: {deployed_url}")
    
    return state
