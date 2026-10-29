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

// Запуск команды в конкретной директории
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

// АВТОГЕНЕРАЦИЯ UV.LOCK
func ensureLockFile(projectDir string) {
	backendDir := filepath.Join(projectDir, "backend_core")
	lockFile := filepath.Join(backendDir, "uv.lock")
	pyprojectFile := filepath.Join(backendDir, "pyproject.toml")

	// Если лок-файл есть, ничего не делаем
	if _, err := os.Stat(lockFile); err == nil {
		return
	}

	// Если нет pyproject.toml, то это не наш проект
	if _, err := os.Stat(pyprojectFile); os.IsNotExist(err) {
		fmt.Println("[ERROR] Не найден backend_core/pyproject.toml!")
		os.Exit(1)
	}

	fmt.Println("\n[WARN] Файл uv.lock не найден. Генерируем автоматически...")
	fmt.Println("[INFO] Это может занять около минуты...")

	// Запускаем временный контейнер для генерации
	err := runCmd(projectDir, "docker", "run", "--rm",
		"-v", fmt.Sprintf("%s:/app", backendDir),
		"-w", "/app",
		"-e", "UV_PROJECT_ENVIRONMENT=/tmp/uv-venv",
		"python:3.12-slim",
		"sh", "-c", "pip install --quiet uv==0.5.11 && uv lock")

	if err != nil {
		fmt.Println("\n[ERROR] Не удалось сгенерировать uv.lock.")
		fmt.Println("Проверьте интернет-соединение и доступ Docker к PyPI.")
		os.Exit(1)
	}
	fmt.Println("[OK] uv.lock успешно создан.")
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

	if err := runCmd(".", "docker", "info"); err != nil {
		fmt.Println("\n[ERROR] Docker не запущен. Пожалуйста, запустите Docker Desktop.")
		os.Exit(1)
	}

	exePath, _ := os.Executable()
	projectDir := filepath.Dir(exePath)

	// 1. Проверяем/генерируем uv.lock
	ensureLockFile(projectDir)

	// 2. Создаем .env
	setupEnv(projectDir)

	// 3. Сборка
	fmt.Println("\n[INFO] Сборка и запуск Бэкенда и Базы Данных...")
	dc(projectDir, "down", "--remove-orphans")
	if !dc(projectDir, "up", "-d", "--build") {
		os.Exit(1)
	}

	// 4. Ждем БД и инициализируем
	fmt.Println("\n[INFO] Ожидание запуска базы данных (10 секунд)...")
	time.Sleep(10 * time.Second)

	fmt.Println("\n[INFO] Создание таблиц и администратора...")
	runCmd(projectDir, "docker", "compose", "exec", "-T", "backend", "python", "scripts/manage.py", "init-db")
	runCmd(projectDir, "docker", "compose", "exec", "-T", "backend", "python", "scripts/manage.py", "reset-admin")

	fmt.Println("\n==================================================")
	fmt.Println("  УСТАНОВКА ЗАВЕРШЕНА!")
	fmt.Println("  API и Swagger доступны: http://localhost:8000/docs")
	fmt.Println("==================================================")
	
	reader := bufio.NewReader(os.Stdin)
	fmt.Println("Нажмите Enter для выхода...")
	reader.ReadString('\n')
}