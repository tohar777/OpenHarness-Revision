import './style.css';
import { marked } from "marked"
const form = document.querySelector<HTMLFormElement>("#form");
const prompt = document.querySelector<HTMLInputElement>("#prompt");
const response = document.querySelector<HTMLDivElement>("#response");

if (!form || !prompt || !response) {
    throw new Error("OpenHarness: Required HTML elements not found!");
}

form.addEventListener("submit", async (e: SubmitEvent) => {
    e.preventDefault();

    const message = prompt.value.trim();
    if (message == "/clear"){ 
        response.innerHTML = "";
        prompt.value = ""
        return;
    }
    if (message == "/about"){ 
        response.innerHTML += "<div><img src='/logo.png' style='height:200px;' /> <h4>OpenHarness v1.0 create by tohar zioni (C) 2026</h4></div>";
        prompt.value = ""
        return;
    }
    if (!message) return;

    const messageElement = document.createElement("div");
    const userLabel = document.createElement("strong");

    userLabel.textContent = "You";
    messageElement.append(userLabel, document.createTextNode(`: ${message}`));

    response.appendChild(messageElement);

    prompt.value = "";

    const thinking = document.createElement("div");
    thinking.textContent = "OpenHarness is thinking...";
    thinking.style.color = "white";

    response.appendChild(thinking);

    try {
        const result = await fetch("http://127.0.0.1:5000/api/sendrequest", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ prompt: message })
        });

        console.log("HTTP status:", result.status);

        const data = await result.json();

        console.log("Server returned:", data);

        if (!result.ok) {
            throw new Error(data.error || "Request failed");
        }
        const htmlConvert = marked.parse(`${data.response}`)
        const aiMessage = document.createElement("div");
        aiMessage.innerHTML = `<strong>OpenHarness</strong>: ${htmlConvert}`;
        aiMessage.style.color = "white";

        response.appendChild(aiMessage);

    } catch (error) {
        console.error("OpenHarness error:", error);

        const errorMessage = document.createElement("div");
        errorMessage.textContent = `OpenHarness Error: ${
            error instanceof Error ? error.message : "Unknown error"
        }`;

        errorMessage.style.color = "red";
        response.appendChild(errorMessage);

    } finally {
        thinking.remove();
    }
});
