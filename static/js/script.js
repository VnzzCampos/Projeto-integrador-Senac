console.log("Sistema iniciado.");


// CAPTURA DOS ELEMENTOS

let senha = document.getElementById("senha");
let confirmar = document.getElementById("confirmar");
let nome = document.getElementById("nome");
let nascimento = document.getElementById("nascimento")
let email = document.getElementById("email")


let mensagem = document.getElementById("mensagemSenha");
let forcaSenha = document.getElementById("forcaSenha");

let btnCriar = document.getElementById("btnCriar");

let numeroIn = document.getElementById("numeroIn");
let maiusculaIn = document.getElementById("maiusculaIn");
let minusculaIn = document.getElementById("minusculaIn");
let simboloIn = document.getElementById("simboloIn");
let tamanhoIn = document.getElementById("tamanhoIn");
let nomeIn = document.getElementById("nomeIn");
let nascimentoIn = document.getElementById("nascimentoIn");


let hoje = new Date();
let anoAtual = hoje.getFullYear();
let dataSelecionada = new Date(nascimento.value);
let anoNascimento = dataSelecionada.getFullYear();


// CONFIGURAÇÕES INICIAIS

btnCriar.disabled = true;


// EVENTOS

senha.addEventListener("input", verificarSenhas);
confirmar.addEventListener("input", verificarSenhas);
nascimento.addEventListener("change", verificarNascimento);
senha.addEventListener("input", verificarForca);
nome.addEventListener("input", validarFormulario);
email.addEventListener("input", validarFormulario);

// FUNÇÃO AUXILIAR

function atualizarRequisito(elemento, passou, texto){

    if(passou){
        elemento.textContent = "✔ " + texto;
        elemento.style.color = "lime";
    }else{
        elemento.textContent = "✖ " + texto;
        elemento.style.color = "red";
    }

}


// VERIFICAR SENHAS

function verificarSenhas(){

    if(senha.value === "" || confirmar.value === ""){
        mensagem.textContent = "";
        validarFormulario();
        return;
    }

    if(senha.value === confirmar.value){
        mensagem.textContent = "As senhas coincidem.";
        mensagem.style.color = "lime";
    }else{
        mensagem.textContent = "As senhas não coincidem.";
        mensagem.style.color = "red";
    }

    validarFormulario();

}


// VERIFICAR FORÇA DA SENHA

function verificarForca(){

    if(senha.value === ""){

        tamanhoIn.textContent = "";
        numeroIn.textContent = "";
        maiusculaIn.textContent = "";
        minusculaIn.textContent = "";
        simboloIn.textContent = "";
        forcaSenha.textContent = "";

        validarFormulario();
        return;

    }

    atualizarRequisito(
        tamanhoIn,
        senha.value.length >= 8,
        "Mínimo de 8 caracteres"
    );

    atualizarRequisito(
        numeroIn,
        /\d/.test(senha.value),
        "Deve conter pelo menos 1 número"
    );

    atualizarRequisito(
        maiusculaIn,
        /[A-Z]/.test(senha.value),
        "Deve conter pelo menos 1 letra maiúscula"
    );

    atualizarRequisito(
        minusculaIn,
        /[a-z]/.test(senha.value),
        "Deve conter pelo menos 1 letra minúscula"
    );

    atualizarRequisito(
        simboloIn,
        /[!@#$%^&*]/.test(senha.value),
        "Deve conter pelo menos 1 caractere especial"
    );


    validarFormulario();

}


// VALIDAR FORMULÁRIO

function validarFormulario(){

    // Validação do nome
    let partes = nome.value.trim().split(" ");
    let nomeValido = partes.length >= 2;

    if(nome.value === ""){

        nomeIn.textContent = "";

    }else if(nomeValido){

        nomeIn.textContent = "✔ Nome válido";
        nomeIn.style.color = "lime";

    }else{

        nomeIn.textContent = "✖ Informe nome e sobrenome";
        nomeIn.style.color = "red";

    }

    // Validação da senha
    let senhaValida =
        senha.value.length >= 8 &&
        /\d/.test(senha.value) &&
        /[A-Z]/.test(senha.value) &&
        /[a-z]/.test(senha.value) &&
        /[!@#$%^&*]/.test(senha.value);

    // Verifica se as senhas são iguais
    let senhasIguais =
        senha.value === confirmar.value &&
        senha.value !== "";

    
    let emailValido = email.value.trim() !=="";

    // Libera ou bloqueia o botão
    btnCriar.disabled = !(nomeValido && senhaValida && senhasIguais && emailValido);

}

// Verificar ano
function verificarNascimento(){

    if(nascimento.value === ""){
        return;
    }
    let hoje = new Date();
    let anoAtual = hoje.getFullYear();
    let dataSelecionada = new Date(nascimento.value);
    let anoNascimento = dataSelecionada.getFullYear();
    if(anoNascimento > anoAtual){

        alert("O ano de nascimento não pode ser maior que o ano atual.");

        nascimento.value = "";

    }

}