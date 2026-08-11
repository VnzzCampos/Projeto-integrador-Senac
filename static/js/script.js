console.log("Sistema iniciado.");

function abrirMenu() {
    const menu = document.getElementById("menuLateral");
    const botao = document.querySelector(".menu");
    if (!menu || !botao) return;

    const aberto = menu.classList.toggle("ativo");
    botao.classList.toggle("ativo", aberto);
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

document.querySelectorAll('a[href]').forEach((link) => {
    link.addEventListener("click", (evento) => {
        const destino = link.getAttribute("href");
        const mesmaPagina = !destino || destino.startsWith("#") || link.target === "_blank";
        const cliqueModificado = evento.ctrlKey || evento.metaKey || evento.shiftKey || evento.altKey;

        if (mesmaPagina || cliqueModificado || evento.button !== 0) return;

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
