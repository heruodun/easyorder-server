
Private Sub Workbook_Open()
    LoginForm.Show
End Sub



Private Sub Workbook_BeforePrint(Cancel As Boolean)
    On Error GoTo ErrHandler
    RunCodeWithProtection
    Exit Sub

ErrHandler:
    Cancel = True
    MsgBox "打印取消，发生错误: " & Err.Description '展示错误描述
    Application.EnableEvents = True '这条语句非常重要 没有这条语句错误的时候 无法阻断

End Sub

 Sub RunCodeWithProtection()


    Dim ws As Worksheet
    Set ws = ThisWorkbook.Sheets("Sheet1") '更改为您要操作的具体工作表名
    Application.ScreenUpdating = False '关闭屏幕更新
    Application.EnableEvents = False '禁用事件
    Application.Calculation = xlCalculationManual '设置计算为手动
    ws.Protect "481676", UserInterfaceOnly:=True



    SendDataAndGetResponse


    ' 恢复设置

    Application.ScreenUpdating = True
    Application.EnableEvents = True
    Application.Calculation = xlCalculationAutomatic
End Sub


Sub Logout()
    LoginForm.Show 'LoginForm是您的登录表单名称
End Sub


Sub SendDataAndGetResponse()
    Dim ws As Worksheet
    Set ws = ThisWorkbook.Sheets("Sheet1") '假设数据在Sheet1上

    ' 读取A12到F26的内容
    Dim dataRange As Range
    Set dataRange = ws.Range("A12:F26")

    Dim requestData As String
    requestData = RangeToJson(dataRange)

    ' HTTP POST请求
    Dim httpRequest As Object
    Set httpRequest = CreateObject("WinHttp.WinHttpRequest.5.1")
    Dim myUrl As String

    Dim ip As String

    ' 获取环境变量的值
    ip = Environ("ORDER_EASY_SERVER_IP")

    myUrl = "http://" & ip & ":5000/orders" ' 替换为实际的URL

    ' 发送HTTP POST请求
    httpRequest.Open "POST", myUrl, False
    httpRequest.setRequestHeader "Content-Type", "application/json" '确保Content-Type头部正确设置
    httpRequest.Send requestData


    ' 解析HTTP响应
    If httpRequest.Status = 201 Then
        Dim response As String
        response = httpRequest.responseText

        Dim jsonParser As Object
        Set jsonParser = JsonConverter.ParseJson(response) '需要JsonConverter库

        ' 将响应数据写回Excel
        ws.Range("F26").Value = jsonParser("order_id")
        ws.Range("E26").Value = jsonParser("create_time")
        ws.Range("F5").Value = jsonParser("qr_code")

    Else
        MsgBox "Error with response - Status: " & xmlhttp.Status
    End If
    Set httpRequest = Nothing
End Sub

Function RangeToJson(rng As Range) As String
    Dim arr() As Variant
    arr = rng.Value '将范围内的数据读取到数组

    Dim row As Long, col As Long
    Dim JsonString As String
    JsonString = "{""data"":["

    For row = LBound(arr, 1) To UBound(arr, 1)
        JsonString = JsonString & "["
        For col = LBound(arr, 2) To UBound(arr, 2)
            JsonString = JsonString & """" & arr(row, col) & """"
            If col <> UBound(arr, 2) Then JsonString = JsonString & ","
        Next col
        JsonString = JsonString & "]"
        If row <> UBound(arr, 1) Then JsonString = JsonString & ","
    Next row

    JsonString = JsonString & "]}"

    RangeToJson = JsonString
End Function


Function CheckPairs() As Boolean
    Dim i As Integer
    Dim ws As Worksheet
    Set ws = ThisWorkbook.Sheets("Sheet1") ' 修改为你的工作表名

    ' 默认设置为True, 假设所有对都是正确的
    CheckPairs = True

    For i = 15 To 23
        If (IsEmpty(ws.Cells(i, "C")) And Not IsEmpty(ws.Cells(i, "E"))) _
        Or (Not IsEmpty(ws.Cells(i, "C")) And IsEmpty(ws.Cells(i, "E"))) Then
            ' 如果发现一个对不满足条件，则将函数结果设置为 False 并退出循环
            CheckPairs = False
            Exit Function
        End If
    Next i
End Function

