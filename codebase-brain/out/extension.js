"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.activate = activate;
exports.deactivate = deactivate;
const vscode = __importStar(require("vscode"));
const child_process_1 = require("child_process");
const path = __importStar(require("path"));
function activate(context) {
    const statusBar = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 100);
    statusBar.text = 'Brain';
    statusBar.tooltip = 'Codebase Brain';
    statusBar.command = 'codebaseBrain.showDetails';
    statusBar.show();
    context.subscriptions.push(statusBar);
    function runImpact(relPath, workspaceRoot) {
        const cmd = `brain impact --file "${relPath}"`;
        (0, child_process_1.exec)(cmd, { cwd: workspaceRoot }, (err, stdout) => {
            if (stdout && stdout.includes('Risk Level:')) {
                const riskMatch = stdout.match(/Risk Level:\s*(HIGH|MEDIUM|LOW)/);
                const risk = riskMatch ? riskMatch[1] : 'LOW';
                const arrowCount = (stdout.match(/→/g) || []).length;
                if (risk === 'HIGH') {
                    statusBar.text = `Brain: HIGH RISK — ${arrowCount} files affected`;
                    statusBar.color = undefined;
                    statusBar.backgroundColor = new vscode.ThemeColor('statusBarItem.errorBackground');
                }
                else if (risk === 'MEDIUM') {
                    statusBar.text = `Brain: MEDIUM RISK — ${arrowCount} files affected`;
                    statusBar.color = undefined;
                    statusBar.backgroundColor = new vscode.ThemeColor('statusBarItem.warningBackground');
                }
                else {
                    statusBar.text = `Brain: LOW RISK — ${arrowCount} files affected`;
                    // VS Code has no built-in green statusBarItem background,
                    // so use a custom green color on default background
                    statusBar.color = new vscode.ThemeColor('terminal.ansiGreen');
                    statusBar.backgroundColor = undefined;
                }
                statusBar.tooltip = stdout;
                return;
            }
            if (stdout && stdout.includes('not found')) {
                statusBar.text = 'Brain: not tracked';
                statusBar.color = undefined;
                statusBar.backgroundColor = undefined;
                statusBar.tooltip = stdout;
                return;
            }
            statusBar.text = 'Brain: run brain start';
            statusBar.color = undefined;
            statusBar.backgroundColor = undefined;
        });
    }
    function analyzeCurrentFile() {
        const editor = vscode.window.activeTextEditor;
        if (!editor || editor.document.uri.scheme !== 'file') {
            return;
        }
        const filepath = editor.document.fileName;
        const folder = vscode.workspace.getWorkspaceFolder(editor.document.uri);
        if (!folder) {
            return;
        }
        const workspaceRoot = folder.uri.fsPath;
        const codeExts = ['.py', '.js', '.ts', '.java', '.go', '.rs', '.cs'];
        if (!codeExts.some(ext => filepath.endsWith(ext))) {
            statusBar.text = 'Brain';
            statusBar.color = undefined;
            statusBar.backgroundColor = undefined;
            return;
        }
        const relPath = path.relative(workspaceRoot, filepath).replace(/\\/g, '/');
        if (relPath.startsWith('..')) {
            return;
        }
        statusBar.text = 'Brain: checking...';
        runImpact(relPath, workspaceRoot);
    }
    const showDetails = vscode.commands.registerCommand('codebaseBrain.showDetails', () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor)
            return;
        const folder = vscode.workspace.getWorkspaceFolder(editor.document.uri);
        if (!folder)
            return;
        const workspaceRoot = folder.uri.fsPath;
        const relPath = path.relative(workspaceRoot, editor.document.fileName).replace(/\\/g, '/');
        (0, child_process_1.exec)(`brain impact --file "${relPath}"`, { cwd: workspaceRoot }, (err, stdout) => {
            const output = vscode.window.createOutputChannel('Codebase Brain');
            output.clear();
            output.appendLine(stdout || 'No data.');
            output.show();
        });
    });
    vscode.window.onDidChangeActiveTextEditor(() => analyzeCurrentFile(), null, context.subscriptions);
    vscode.workspace.onDidSaveTextDocument(() => analyzeCurrentFile(), null, context.subscriptions);
    analyzeCurrentFile();
    context.subscriptions.push(showDetails);
}
function deactivate() { }
//# sourceMappingURL=extension.js.map