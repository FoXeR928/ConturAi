package main

import (
	"bufio"
	"crypto/rand"
	"fmt"
	"math/big"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"time"
)

// Запуск команды
func runCmd(dir string, name string, args ...string) error {
	cmd := exec.Command(name, args...)
	cmd.Dir = dir
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	cmd.Stdin = os.Stdin
	return cmd.Run()
}

// Обертка для docker compose
func dc(projectDir string, args ...string) bool {
	composeFile := filepath.Join(projectDir, "docker-compose.yml")
	fullArgs := append([]string{"compose", "-f", composeFile}, args...)
	err := runCmd(projectDir, "docker", fullArgs...)
	if err != nil {
		fmt.Printf("\n[ERROR] Ошибка Docker Compose: %v\n", err)
		return false
	}
	return true
}

// Генерация пароля
func generatePassword(length int) string {
	const chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
	result := make([]byte, length)
	for i := range result {
		num, _ := rand.Int(rand.Reader, big.NewInt(int64(len(chars))))
		result[i] = chars[num.Int64()]
	}
	return string(result)
}

// Создание .env
func setupEnv(projectDir string) {
	envPath := filepath.Join(projectDir, ".env")
	examplePath := filepath.Join(projectDir, ".env.example")

	if _, err := os.Stat(envPath); err == nil {
		fmt.Println("[INFO] Файл .env уже существует. Используем текущие настройки.")
		return
	}

	fmt.Println("[INFO] Создание нового .env с безопасным паролем...")
	password := generatePassword(24)
	content, err := os.ReadFile(examplePath)
	if err != nil {
		fmt.Println("[ERROR] Не найден .env.example!")
		os.Exit(1)
	}

	newContent := strings.Replace(string(content), "DB_PASSWORD=CHANGE_ME", "DB_PASSWORD="+password, 1)
	os.WriteFile(envPath, []byte(newContent), 0644)
	fmt.Println("[OK] Файл .env создан.")
}

func main() {
	fmt.Println("==================================================")
	fmt.Println("  ConturAI Core - Установщик (v3.0)")
	fmt.Println("==================================================")

	// 1. Проверка Docker
	if err := runCmd(".", "docker", "info"); err != nil {
		fmt.Println("\n[ERROR] Docker не запущен. Пожалуйста, запустите Docker Desktop.")
		os.Exit(1)
	}

	// Получаем путь
	exePath, _ := os.Executable()
	projectDir := filepath.Dir(exePath)

	// 2. Создаем .env
	setupEnv(projectDir)

	// 3. Запускаем сборку
	fmt.Println("\n[INFO] Сборка и запуск контейнеров (это может занять пару минут)...")
	dc(projectDir, "down", "--remove-orphans")
	if !dc(projectDir, "up", "-d", "--build") {
		os.Exit(1)
	}

	// 4. Ждем БД
	fmt.Println("\n[INFO] Ожидание запуска базы данных (10 секунд)...")
	time.Sleep(10 * time.Second)

	// 5. Инициализация БД и админа
	fmt.Println("\n[INFO] Создание таблиц и администратора...")
	// Вызываем manage.py внутри контейнера
	runCmd(projectDir, "docker", "compose", "exec", "-T", "backend", "python", "scripts/manage.py", "init-db")
	runCmd(projectDir, "docker", "compose", "exec", "-T", "backend", "python", "scripts/manage.py", "reset-admin")

	fmt.Println("\n==================================================")
	fmt.Println("  УСТАНОВКА ЗАВЕРШЕНА!")
	fmt.Println("  Откройте: http://localhost:3000")
	fmt.Println("  (Данные для входа смотрите в логах выше)")
	fmt.Println("==================================================")
	
	reader := bufio.NewReader(os.Stdin)
	fmt.Println("Нажмите Enter для выхода...")
	reader.ReadString('\n')
}