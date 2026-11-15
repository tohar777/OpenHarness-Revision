import './style.css';

interface View {
    name: string;
    id: string;
    func: () => void;
}

import { marked } from "marked"
const form = document.querySelector<HTMLFormElement>("#form");
const prompt = document.querySelector<HTMLInputElement>("#prompt");
const response = document.querySelector<HTMLDivElement>("#response");
const openView = document.querySelector<HTMLButtonElement>("#openView");
const viewList = document.querySelector<HTMLDivElement>("#viewList");
let isViewOpen:boolean = false;
console.log("OpenView:", openView);
const viewTest: View[] = [
    {
        name: "Hello World View",
        id: "hello_test",
        func: () => {
            console.log("Hello World View opened!");
        }
    }
];
if (!form || !prompt || !response) {
    throw new Error("OpenHarness: Required HTML elements not found!");
}


openView?.addEventListener("click", (e: Event) => {
    e.preventDefault();

    if (!viewList) return;

    isViewOpen = !isViewOpen;
    viewList.innerHTML = "";

    if (isViewOpen) {
        viewList.style.position = "relative";
        viewList.style.display = "block";
        viewList.style.width= "80%";
        viewList.style.left = "10%";
        viewList.style.top = "10px";
        viewList.style.border = "3px solid rgb(155, 155, 155)";
        viewList.style.borderRadius = "5px";
        for (const view of viewTest) {
            const button = document.createElement("button");
            button.className = "navButton";
            button.id = view.id;
            button.textContent = view.name;
            button.addEventListener("click", view.func);

            viewList.appendChild(button);
        }
    } else {
        viewList.style.display = "none";
    }
});

form.addEventListener("submit", async (e: SubmitEvent) => {
    e.preventDefault();

    const message = prompt.value.trim();
    if (message == "/clear"){ 
        response.innerHTML = "";
        prompt.value = ""
        return;
    }
    if (message == "/about"){ 
        response.innerHTML += "<div><img src='/logo.png' style='height:200px;' /> <h4>OpenHarness v1.1 create by tohar zioni (C) 2026</h4></div>";
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
    const startTime = Date.now();

    const timer = setInterval(() => {
        const secondsPassed = Math.floor(
            (Date.now() - startTime) / 1000
        );

        thinking.textContent = `OpenHarness is thinking (${secondsPassed}s)...`;
        thinking.style.color = "white";
    }, 1000);
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
        clearInterval(timer)
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
