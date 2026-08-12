console.log("Sistema iniciado.");

const fundoMenu = document.createElement("div");
fundoMenu.className = "menu-fundo";
fundoMenu.setAttribute("aria-hidden", "true");
document.body.appendChild(fundoMenu);

const modalSaida = document.createElement("div");
modalSaida.className = "modal-saida";
modalSaida.innerHTML = `
    <div class="modal-saida-caixa" role="dialog" aria-modal="true" aria-labelledby="titulo-saida">
        <div class="modal-icone" aria-hidden="true">↩</div>
        <div><p class="modal-legenda">Encerrar sessão</p><h2 id="titulo-saida">Deseja sair da sua conta?</h2><p>Você precisará entrar novamente para acessar o sistema.</p></div>
        <div class="modal-acoes"><button type="button" class="modal-cancelar">Continuar aqui</button><button type="button" class="modal-confirmar">Sair do sistema</button></div>
    </div>`;
document.body.appendChild(modalSaida);

function confirmarSaida() {
    return new Promise((resolver) => {
        const cancelar = modalSaida.querySelector(".modal-cancelar");
        const confirmar = modalSaida.querySelector(".modal-confirmar");
        const finalizar = (resposta) => {
            modalSaida.classList.remove("ativo");
            cancelar.removeEventListener("click", cancelarSaida);
            confirmar.removeEventListener("click", confirmarSaidaAgora);
            modalSaida.removeEventListener("click", fecharNoFundo);
            resolver(resposta);
        };
        const cancelarSaida = () => finalizar(false);
        const confirmarSaidaAgora = () => finalizar(true);
        const fecharNoFundo = (evento) => { if (evento.target === modalSaida) finalizar(false); };
        cancelar.addEventListener("click", cancelarSaida);
        confirmar.addEventListener("click", confirmarSaidaAgora);
        modalSaida.addEventListener("click", fecharNoFundo);
        modalSaida.classList.add("ativo");
        confirmar.focus();
    });
}

function padronizarMenuLateral() {
    const menu = document.getElementById("menuLateral");
    if (!menu) return;

    const linksAtuais = Array.from(menu.querySelectorAll("a")).map((link) => link.getAttribute("href"));
    const administrador = linksAtuais.some((href) => ["/gestao", "/ofertas", "/turmas/nova"].includes(href));
    const podeLancarFrequencia = administrador || linksAtuais.includes("/frequencia");
    const links = [
        ["/inicio", "⌂", "Início"],
        ["/comunicacao", "✦", "Materiais e avisos"],
        ["/escala", "◷", "Escala de professores"],
        ["/desempenho", "↗", "Desempenho das turmas"],
        ...(podeLancarFrequencia ? [["/frequencia", "✓", "Frequência"]] : []),
        ...(administrador ? [
            ["/alunos/cadastrar", "♙", "Cadastrar alunos"],
            ["/turmas/nova", "▦", "Turmas"],
            ["/ofertas", "R$", "Ofertas"],
            ["/relatorios/turmas", "▤", "Relatórios"],
            ["/gestao", "⚙", "Gestão"]
        ] : []),
        ["/sair", "↩", "Sair"]
    ];

    menu.innerHTML = `
        <p class="menu-titulo">Navegação</p>
        <div class="menu-links">${links.map(([href, icone, texto]) => `
            <a href="${href}" class="${window.location.pathname === href ? "atual" : ""}">
                <span class="menu-icone" aria-hidden="true">${icone}</span><span>${texto}</span>
            </a>`).join("")}
        </div>`;
}

padronizarMenuLateral();

// Ao voltar pelo navegador, a página pode ser restaurada do cache com a
// animação de saída ainda ativa. Removê-la evita a tela somente com o fundo.
window.addEventListener("pageshow", () => {
    document.body.classList.remove("pagina-saindo");
});

function abrirMenu() {
    const menu = document.getElementById("menuLateral");
    const botao = document.querySelector(".menu");
    if (!menu || !botao) return;

    const aberto = menu.classList.toggle("ativo");
    botao.classList.toggle("ativo", aberto);
    fundoMenu.classList.toggle("ativo", aberto);
    botao.setAttribute("aria-expanded", String(aberto));
    botao.setAttribute("aria-label", aberto ? "Fechar menu" : "Abrir menu");
}

document.querySelectorAll(".menu").forEach((botao) => {
    botao.setAttribute("aria-expanded", "false");
    botao.addEventListener("keydown", (evento) => {
        if (evento.key === "Enter" || evento.key === " ") {
            evento.preventDefault();
            abrirMenu();
        }
    });
});

document.querySelectorAll(".navbar h2").forEach((marca) => {
    marca.setAttribute("role", "link");
    marca.setAttribute("tabindex", "0");
    marca.setAttribute("aria-label", "Voltar ao início");
    const voltarAoInicio = () => {
        if (window.location.pathname !== "/inicio") {
            document.body.classList.add("pagina-saindo");
            window.setTimeout(() => { window.location.href = "/inicio"; }, 220);
        }
    };
    marca.addEventListener("click", voltarAoInicio);
    marca.addEventListener("keydown", (evento) => {
        if (evento.key === "Enter" || evento.key === " ") {
            evento.preventDefault();
            voltarAoInicio();
        }
    });
});

fundoMenu.addEventListener("click", abrirMenu);

document.addEventListener("keydown", (evento) => {
    if (evento.key === "Escape" && document.getElementById("menuLateral")?.classList.contains("ativo")) {
        abrirMenu();
    }
    if (evento.key === "Escape") {
        document.querySelectorAll(".menu-cargo.ativo").forEach((menu) => {
            menu.classList.remove("ativo");
            menu.querySelector(".usuario-menu")?.setAttribute("aria-expanded", "false");
        });
    }
});

document.querySelectorAll(".usuario-menu").forEach((botao) => {
    botao.addEventListener("click", () => {
        const menuCargo = botao.closest(".menu-cargo");
        const estavaAberto = menuCargo.classList.contains("ativo");
        document.querySelectorAll(".menu-cargo.ativo").forEach((menu) => menu.classList.remove("ativo"));
        menuCargo.classList.toggle("ativo", !estavaAberto);
        botao.setAttribute("aria-expanded", String(!estavaAberto));
    });
});

document.addEventListener("click", (evento) => {
    if (!evento.target.closest(".menu-cargo")) {
        document.querySelectorAll(".menu-cargo.ativo").forEach((menu) => {
            menu.classList.remove("ativo");
            menu.querySelector(".usuario-menu")?.setAttribute("aria-expanded", "false");
        });
    }
});

function filtrarItens(campo, itens, textoDoItem) {
    if (!campo) return;
    campo.addEventListener("input", () => {
        const termo = campo.value.trim().toLocaleLowerCase("pt-BR");
        itens.forEach((item) => {
            item.hidden = Boolean(termo) && !textoDoItem(item).includes(termo);
        });
    });
}

filtrarItens(
    document.getElementById("pesquisa-usuarios"),
    document.querySelectorAll(".gestao-bloco tbody tr"),
    (linha) => linha.textContent.toLocaleLowerCase("pt-BR")
);

const pesquisaAluno = document.getElementById("pesquisa-aluno");
const listaUsuariosAluno = document.getElementById("lista-usuarios-aluno");
if (pesquisaAluno && listaUsuariosAluno) {
    pesquisaAluno.addEventListener("input", () => {
        const termo = pesquisaAluno.value.trim().toLocaleLowerCase("pt-BR");
        listaUsuariosAluno.querySelectorAll(".conta-checkbox").forEach((conta) => {
            conta.hidden = Boolean(termo) && !conta.textContent.toLocaleLowerCase("pt-BR").includes(termo);
        });
    });
}

document.querySelectorAll('a[href]').forEach((link) => {
    link.addEventListener("click", async (evento) => {
        const destino = link.getAttribute("href");
        const mesmaPagina = !destino || destino.startsWith("#") || link.target === "_blank";
        const cliqueModificado = evento.ctrlKey || evento.metaKey || evento.shiftKey || evento.altKey;

        if (mesmaPagina || cliqueModificado || evento.button !== 0) return;

        if (destino === "/sair") {
            evento.preventDefault();
            if (!await confirmarSaida()) return;
        }

        evento.preventDefault();
        document.body.classList.add("pagina-saindo");
        window.setTimeout(() => { window.location.href = destino; }, 220);
    });
});

const senha = document.getElementById("senha");
const confirmar = document.getElementById("confirmar");
const nome = document.getElementById("nome");
const nascimento = document.getElementById("nascimento");
const email = document.getElementById("email");
const btnCriar = document.getElementById("btnCriar");

if (senha && confirmar && nome && nascimento && email && btnCriar) {
    const mensagem = document.getElementById("mensagemSenha");
    const requisitos = {
        tamanho: document.getElementById("tamanhoIn"),
        numero: document.getElementById("numeroIn"),
        maiuscula: document.getElementById("maiusculaIn"),
        minuscula: document.getElementById("minusculaIn"),
        simbolo: document.getElementById("simboloIn")
    };

    function atualizarRequisito(elemento, passou, texto) {
        if (!elemento) return;
        elemento.textContent = `${passou ? "✓" : "✕"} ${texto}`;
        elemento.style.color = passou ? "lime" : "red";
    }

    function validarFormulario() {
        const partes = nome.value.trim().split(/\s+/);
        const nomeValido = nome.value.trim() !== "" && partes.length >= 2;
        const senhaValida = senha.value.length >= 8 && /\d/.test(senha.value)
            && /[A-Z]/.test(senha.value) && /[a-z]/.test(senha.value)
            && /[!@#$%^&*]/.test(senha.value);
        const senhasIguais = senha.value !== "" && senha.value === confirmar.value;
        btnCriar.disabled = !(nomeValido && senhaValida && senhasIguais && email.value.trim() !== "");
    }

    function verificarForca() {
        atualizarRequisito(requisitos.tamanho, senha.value.length >= 8, "Mínimo de 8 caracteres");
        atualizarRequisito(requisitos.numero, /\d/.test(senha.value), "Deve conter pelo menos 1 número");
        atualizarRequisito(requisitos.maiuscula, /[A-Z]/.test(senha.value), "Deve conter pelo menos 1 letra maiúscula");
        atualizarRequisito(requisitos.minuscula, /[a-z]/.test(senha.value), "Deve conter pelo menos 1 letra minúscula");
        atualizarRequisito(requisitos.simbolo, /[!@#$%^&*]/.test(senha.value), "Deve conter pelo menos 1 caractere especial");
    }

    function verificarSenhas() {
        if (mensagem) {
            mensagem.textContent = confirmar.value ? (senha.value === confirmar.value ? "As senhas coincidem." : "As senhas não coincidem.") : "";
            mensagem.style.color = senha.value === confirmar.value ? "lime" : "red";
        }
        validarFormulario();
    }

    btnCriar.disabled = true;
    senha.addEventListener("input", () => { verificarForca(); verificarSenhas(); });
    confirmar.addEventListener("input", verificarSenhas);
    nome.addEventListener("input", validarFormulario);
    email.addEventListener("input", validarFormulario);
    nascimento.addEventListener("change", () => {
        if (nascimento.value && new Date(nascimento.value).getFullYear() > new Date().getFullYear()) {
            alert("O ano de nascimento não pode ser maior que o ano atual.");
            nascimento.value = "";
        }
    });
}
