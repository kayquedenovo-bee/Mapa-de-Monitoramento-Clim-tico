const previsaoMap = new Map();

document.addEventListener('DOMContentLoaded', () => {

    // Configurações Iniciais
    if (typeof tailwind !== 'undefined') {
        tailwind.config = { theme: { extend: { fontFamily: { sans: ['Inter', 'sans-serif'], }, } } }
    }

    // Inicialização do Mapa
    const map = L.map('map', { zoomControl: false }).setView([-16.679, -49.255], 7);

    // Variável tileLayer
    const tileLayer = L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; OpenStreetMap &copy; CARTO',
        maxZoom: 19
    }).addTo(map);

    L.control.zoom({ position: 'topright' }).addTo(map);

    // Grupos de Camadas
    const rainGroup = L.layerGroup().addTo(map);
    const windGroup = L.layerGroup().addTo(map);
    const markerGroup = L.layerGroup();

    let layerMunicipios = null;
    let layerUF = null;

    // Helper de Texto
    function normalizar(nome) {
        if (!nome) return '';
        return nome.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toUpperCase();
    }

    // --- CARREGAMENTO ---
    function carregarMapas() {
        if (typeof geoEstado === 'undefined' || typeof geoMunicipios === 'undefined') {
            console.error("ERRO: GeoJSON não carregado.");
            return;
        }

        layerUF = L.geoJSON(geoEstado, {
            style: { color: "#111827", weight: 2, fillOpacity: 0.0, interactive: false }
        }).addTo(map);
        map.fitBounds(layerUF.getBounds());

        layerMunicipios = L.geoJSON(geoMunicipios, {
            style: { color: "#4b5563", weight: 0.5, fillOpacity: 0.0, opacity: 0.5 },
            onEachFeature: (feature, layer) => {
                layer.bindTooltip(feature.properties.NM_MUN, { className: 'custom-tooltip' });
                layer.on({
                    mouseover: (e) => e.target.setStyle({ weight: 2, color: "#111827", fillOpacity: 0.2 }),
                    mouseout: (e) => {
                        const val = e.target.feature.properties.current_value || 0;
                        const tipo = e.target.feature.properties.current_type || 'chuva';
                        if (val > 0) {
                            e.target.setStyle(tipo === 'chuva' ? getEstiloChuva(val) : getEstiloVento(val));
                        } else {
                            layerMunicipios.resetStyle(e.target);
                        }
                    },
                    click: (e) => abrirPopup(e, feature.properties.NM_MUN)
                });
            }
        });
        aplicarFiltros();
    }

    // --- DADOS ---
    if (typeof previsaoCompleta !== 'undefined') {
        previsaoCompleta.forEach(item => {
            const dadosPorData = new Map();
            item.dados.forEach(dia => dadosPorData.set(dia.data, dia));
            previsaoMap.set(normalizar(item.municipio), dadosPorData);
        });

        const container = document.getElementById('date-filter-container');
        if (previsaoCompleta.length > 0 && container) {
            const datas = previsaoCompleta[0].dados.map(d => d.data);

            const elData = document.getElementById('data-atualizacao');
            if (elData) elData.innerText = `Atualizado em: ${datas[0]}`;

            container.innerHTML = datas.map((date, i) => `
                <div class="flex items-center">
                    <input id="dia${i}" name="diasemana" type="radio" value="${date}" class="h-4 w-4 text-blue-600" ${i===0?'checked':''}>
                    <label for="dia${i}" class="ml-3 text-sm text-gray-900 cursor-pointer">${date}</label>
                </div>
            `).join('');
            container.addEventListener('change', aplicarFiltros);
        }

        const inputsTipo = document.querySelectorAll('input[name="tipoDado"]');
        inputsTipo.forEach(input => {
            input.addEventListener('change', aplicarFiltros);
        });
    }

    if (typeof municipioCoordenadas !== 'undefined') {
        for (const [nome, coords] of Object.entries(municipioCoordenadas)) {
            L.marker(coords).bindTooltip(nome, { className: 'custom-tooltip' }).addTo(markerGroup);
        }
    }

    // --- FUNÇÕES UI ---
    function getEstiloChuva(v) {
        if (v < 5) return { fillColor: "#bfdbfe", fillOpacity: 0.6, color: "#bfdbfe", weight: 1 };
        if (v < 10) return { fillColor: "#fb923c", fillOpacity: 0.7, color: "#fb923c", weight: 1 };
        if (v < 20) return { fillColor: "#dc2626", fillOpacity: 0.8, color: "#dc2626", weight: 1 };
        return { fillColor: "#1f2937", fillOpacity: 0.85, color: "#1f2937", weight: 1 };
    }

    function getEstiloVento(v) {
        if (v < 20) return { fillColor: "#a7f3d0", fillOpacity: 0.7, color: "#a7f3d0", weight: 1 };
        if (v < 35) return { fillColor: "#fde047", fillOpacity: 0.7, color: "#fde047", weight: 1 };
        if (v < 45) return { fillColor: "#f97316", fillOpacity: 0.7, color: "#f97316", weight: 1 };
        return { fillColor: "#be123c", fillOpacity: 0.8, color: "#be123c", weight: 1 };
    }

    function aplicarFiltros() {
        if (!layerMunicipios) return;

        const diaEl = document.querySelector('input[name="diasemana"]:checked');
        if (!diaEl) return;
        const dia = diaEl.value;

        const tipoEl = document.querySelector('input[name="tipoDado"]:checked');
        const tipo = tipoEl ? tipoEl.value : 'chuva';

        atualizarTextoAviso(dia);

        document.getElementById('legenda-chuva').classList.toggle('hidden', tipo !== 'chuva');
        document.getElementById('legenda-vento').classList.toggle('hidden', tipo !== 'vento');

        const dadosAtuais = {};
        for (const [mun, dados] of previsaoMap) {
            const d = dados.get(dia);
            if (d) dadosAtuais[mun] = (tipo === 'chuva' ? d.chuva_mm : d.vento_kmh);
        }

        layerMunicipios.eachLayer(layer => {
            const nome = normalizar(layer.feature.properties.NM_MUN);
            const valor = dadosAtuais[nome] || 0;
            layer.feature.properties.current_value = valor;
            layer.feature.properties.current_type = tipo;

            if (valor > 0) {
                layer.setStyle(tipo === 'chuva' ? getEstiloChuva(valor) : getEstiloVento(valor));
                layer.bindTooltip(`${layer.feature.properties.NM_MUN}: ${valor} ${tipo==='chuva'?'mm':'km/h'}`, { className: 'custom-tooltip' });
            } else {
                layerMunicipios.resetStyle(layer);
                layer.bindTooltip(layer.feature.properties.NM_MUN, { className: 'custom-tooltip' });
            }
        });

        atualizarRanking(dadosAtuais, tipo);
        atualizarCamadas(tipo);
    }

    function atualizarTextoAviso(dia) {
        const conteudo = document.getElementById('texto-avisos-conteudo');
        if (!conteudo) return;

        if (typeof avisosPorDia !== 'undefined' && avisosPorDia[dia]) {
            conteudo.innerText = avisosPorDia[dia];
            conteudo.classList.remove('border-gray-400', 'text-gray-500');
            conteudo.classList.add('border-red-500', 'text-gray-800');
        } else {
            conteudo.innerText = "Sem avisos específicos para esta data.";
            conteudo.classList.remove('border-red-500', 'text-gray-800');
            conteudo.classList.add('border-gray-400', 'text-gray-500');
        }
    }

    function atualizarRanking(dados, tipo) {
        const list = document.getElementById('top-ranking-list');
        if (!list) return;
        const sorted = Object.entries(dados).filter(x => x[1] > 0).sort((a, b) => b[1] - a[1]).slice(0, 3);
        const unit = tipo === 'chuva' ? 'mm' : 'km/h';
        list.innerHTML = sorted.length === 0 ? '<li>Sem dados.</li>' : sorted.map(([n, v]) => `
            <li class="flex justify-between border-b border-gray-100 pb-1 text-xs">
                <span class="capitalize">${n.toLowerCase()}</span><span class="font-bold">${v.toFixed(1)} ${unit}</span>
            </li>`).join('');
    }

    function atualizarCamadas(tipo) {
        const active = tipo === 'chuva' ? rainGroup : windGroup;
        const inactive = tipo === 'chuva' ? windGroup : rainGroup;
        inactive.clearLayers();
        if (layerMunicipios) active.addLayer(layerMunicipios);
        if (layerUF) layerUF.bringToFront();
    }

    function abrirPopup(e, nome) {
        const diaEl = document.querySelector('input[name="diasemana"]:checked');
        if (!diaEl) return;
        const dia = diaEl.value;

        const dadosMunicipio = previsaoMap.get(normalizar(nome));
        const dados = dadosMunicipio ? dadosMunicipio.get(dia) : null;

        let html = `<h4 class="font-bold mb-2">${nome}</h4>`;
        html += dados ? `<div class="text-sm"><p class="mb-2">Data: <strong>${dia}</strong></p>
            <div class="flex justify-between border-b py-1"><span>Chuva:</span> <b>${dados.chuva_mm} mm</b></div>
            <div class="flex justify-between py-1"><span>Vento:</span> <b>${dados.vento_kmh} km/h</b></div></div>` :
            `<p class="text-xs text-gray-500">Sem previsão.</p>`;
        L.popup().setLatLng(e.latlng).setContent(html).openOn(map);
    }

    const btnSearch = document.getElementById('search-btn');
    const inputSearch = document.getElementById('search-input');
    const errorMsg = document.getElementById('search-error');

    // === FUNÇÃO DE BUSCA INTELIGENTE (CORRIGIDA) ===
    function buscar() {
        if (!inputSearch) return;
        const termo = normalizar(inputSearch.value);
        if (!termo) return;

        let achou = false;

        // 1. TENTATIVA DE MATCH EXATO (PRIORIDADE)
        // Isso impede que "GOIANIA" selecione "APARECIDA DE GOIANIA"

        // Verifica nos marcadores (Exato)
        if (typeof municipioCoordenadas !== 'undefined') {
            for (const [nome, latlng] of Object.entries(municipioCoordenadas)) {
                if (normalizar(nome) === termo) { // Verifica IGUALDADE
                    map.flyTo(latlng, 12);
                    achou = true;
                    break;
                }
            }
        }

        // Verifica no GeoJSON (Exato)
        if (!achou && layerMunicipios) {
            layerMunicipios.eachLayer(l => {
                if (achou) return;
                if (normalizar(l.feature.properties.NM_MUN) === termo) { // Verifica IGUALDADE
                    map.fitBounds(l.getBounds());
                    l.openPopup(); // Abre o popup para confirmar que achou o certo
                    achou = true;
                }
            });
        }

        // 2. TENTATIVA DE MATCH PARCIAL (FALLBACK)
        // Só executa se o passo 1 (exato) falhou. Aqui a lógica é "contém".
        if (!achou) {
            // Verifica nos marcadores (Parcial)
            if (typeof municipioCoordenadas !== 'undefined') {
                for (const [nome, latlng] of Object.entries(municipioCoordenadas)) {
                    if (normalizar(nome).includes(termo)) {
                        map.flyTo(latlng, 12);
                        achou = true;
                        break;
                    }
                }
            }
            // Verifica no GeoJSON (Parcial)
            if (!achou && layerMunicipios) {
                layerMunicipios.eachLayer(l => {
                    if (achou) return;
                    if (normalizar(l.feature.properties.NM_MUN).includes(termo)) {
                        map.fitBounds(l.getBounds());
                        achou = true;
                    }
                });
            }
        }

        if (errorMsg) errorMsg.classList.toggle('hidden', achou);
    }

    if (btnSearch) btnSearch.addEventListener('click', buscar);
    if (inputSearch) inputSearch.addEventListener('keypress', e => { if (e.key === 'Enter') buscar() });

    const toggleBtn = document.getElementById('toggle-sidebar-btn');
    const sidebar = document.getElementById('sidebar');
    if (toggleBtn && sidebar) {
        toggleBtn.addEventListener('click', () => {
            sidebar.classList.toggle('w-0');
            sidebar.classList.toggle('p-0');
            sidebar.classList.toggle('overflow-hidden');
            sidebar.classList.toggle('w-80');
            sidebar.classList.toggle('p-6');
            setTimeout(() => map.invalidateSize(), 300);
        });
    }

    const modal = document.getElementById('modal-avisos');
    const btnAbrirModal = document.getElementById('btn-avisos');
    const btnFecharModal = document.getElementById('btn-fechar-avisos');
    const btnFecharRodape = document.getElementById('btn-fechar-rodape');

    function toggleModal() { if (modal) modal.classList.toggle('hidden'); }
    if (btnAbrirModal) btnAbrirModal.addEventListener('click', toggleModal);
    if (btnFecharModal) btnFecharModal.addEventListener('click', toggleModal);
    if (btnFecharRodape) btnFecharRodape.addEventListener('click', toggleModal);
    if (modal) modal.addEventListener('click', e => { if (e.target === modal) toggleModal(); });

    // Agora garantimos que tileLayer existe, pois foi definido com 'const' lá no início
    L.control.layers({ "Mapa Base": tileLayer }, { "Chuva": rainGroup, "Vento": windGroup, "Marcadores": markerGroup }, { position: 'topright' }).addTo(map);

    carregarMapas();
});