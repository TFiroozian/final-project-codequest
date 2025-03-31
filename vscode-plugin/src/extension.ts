import * as vscode from 'vscode';

// Define the expected shape of the API response
interface ApiResponse {
	markdown?: string;
	errors?: string[];
  }

export function activate(context: vscode.ExtensionContext) {
	console.log('CodeQuest extension is now active!');

	// Register the "codequest.search" command
	let disposable = vscode.commands.registerCommand('codequest.search', async () => {
		// Prompt the user to enter a query
		const query = await vscode.window.showInputBox({
			prompt: 'Enter your question:',
			placeHolder: 'Type your question here...'
		});

		if (!query) {
			vscode.window.showInformationMessage('No query provided.');
			return;
		}

		// Construct the API URL with the user query
		// const apiUrl = `http://localhost:3000/code/search/?query=${encodeURIComponent(query)}`;
		const apiUrl =  `https://7x377tr6i2.execute-api.us-east-1.amazonaws.com/Prod/code/search/?query=${encodeURIComponent(query)}`;
  		const requestHeaders = new Headers();
		const API_KEY = "";
 		requestHeaders.set('api_key', API_KEY ?? "");

		try {
			// Call the backend API
			const response = await fetch(apiUrl, {
				headers: requestHeaders
			});
			if (!response.ok) {
				const errorText = await response.text();
				vscode.window.showErrorMessage(`API Error: ${errorText}`);
				return;
			}

			// Parse the JSON response and handle any errors
			const json = await response.json() as ApiResponse;
			if (json.errors?.length) {
				vscode.window.showErrorMessage(`API returned errors: ${json.errors.join(', ')}`);
				return;
			}

			const markdown = json.markdown;
			if (!markdown) {
				vscode.window.showInformationMessage('No results found.');
				return;
			}

			// Open a new VSCode editor tab with the Markdown content
			const doc = await vscode.workspace.openTextDocument({
				content: markdown,
				language: 'markdown'
			});

		} catch (error: any) {
			vscode.window.showErrorMessage(`Error fetching API: ${error.message}`);
		}
	});

	// Add the command to the extension's subscriptions
	context.subscriptions.push(disposable);
}

export function deactivate() {}
