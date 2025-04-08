#Requires AutoHotkey v2.0
SetTimer(CheckActiveWindow, 10000) ; Configura un temporizador para ejecutar la función cada 10 segundos
Return                             ; Finaliza la ejecución inicial del script

CheckActiveWindow() {
    xiboTitle := "Xibo"             ; Título de la ventana de Xibo
    activeTitle := WinGetTitle("A") ; Obtiene el título de la ventana activa

    ; Verifica si la ventana activa no es "Xibo"
    If (activeTitle != xiboTitle) {
        If WinExist(xiboTitle) {  ; Verifica si existe la ventana de Xibo
            HWND := WinGetID(xiboTitle) ; Obtiene el identificador de la ventana de Xibo
            WinActivate(HWND)          ; Activa la ventana de Xibo
        }
    }
}