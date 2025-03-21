'use client'
import { useEffect, useRef } from 'react';
import { io } from 'socket.io-client';

function Terminal() {
  const terminalRef = useRef<HTMLDivElement>(null);
  
  useEffect(() => {
    // Use relative URL to work with the proxy from next.config.js
    const socket = io('localhost:5000');
    
    const handleTerminalOutput = (data: { status: string; }) => {
      if (!terminalRef.current) return;
      
      const newLog = document.createElement("p");
      newLog.innerText = data.status;
      
      if (data.status.startsWith("ERROR")) {
        newLog.classList.add("text-red-500"); // Highlight errors in red using Tailwind
      }
      
      terminalRef.current.appendChild(newLog);
      
      // Auto-scroll to bottom
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    };
    
    // Set up event listener
    socket.on("terminal_output", handleTerminalOutput);
    
    // Clean up when component unmounts
    return () => {
      socket.off("terminal_output", handleTerminalOutput);
      socket.disconnect();
    };
  }, []);
  
  return (
    <div className="w-full h-[25vh] fixed bottom-0 left-0 bg-gray-900 text-white p-4 z-[5] shadow-[0_-10px_15px_-3px_rgba(0,0,0,0.1),0_-4px_6px_-4px_rgba(0,0,0,0.1)] overflow-auto">
      <div className="font-bold mb-2">Terminal</div>
      <div 
        id="terminal" 
        ref={terminalRef} 
        className="h-[calc(100%-2rem)] overflow-auto font-mono text-sm"
      >
        {/* Terminal output will be appended here */}
      </div>
    </div>
  );
}

export default Terminal;