package main

import (
	"bufio"
	"crypto/rand"
	"fmt"
	"io"
	"math/big"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"time"
)

func runCmd(dir string, name string, args ...string) error {
	cmd := exec.Command(name, args...)
	cmd.Dir = dir
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	cmd.Stdin = os.Stdin
	return cmd.Run()
}

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

func generatePassword(length int) string {
	const chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
	result := make([]byte, length)
	for i := range result {
		num, _ := rand.Int(rand.Reader, big.NewInt(int64(len(chars))))
		result[i] = chars[num.Int64()]
	}
	return string(result)
}

func findProjectRoot() string {
	exePath, err := os.Executable()
	if err != nil {
		dir, _ := os.Getwd()
		return dir
	}
	dir := filepath.Dir(exePath)

	if _, err := os.Stat(filepath.Join(dir, "templates")); err == nil {
		return dir
	}
	parentDir := filepath.Dir(dir)
	if _, err := os.Stat(filepath.Join(parentDir, "templates")); err == nil {
		return parentDir
	}
	currentDir, _ := os.Getwd()
	if _, err := os.Stat(filepath.Join(currentDir, "templates")); err == nil {
		return currentDir
	}
	return dir
}

// Проверка структуры проекта перед установкой
func checkProjectStructure(projectDir string) {
	// Проверяем бэкенд
	if _, err := os.Stat(filepath.Join(projectDir, "backend_core", "pyproject.toml")); os.IsNotExist(err) {
		fmt.Println("\n[ERROR] Не найдена папка 'backend_core' или файл 'pyproject.toml' внутри неё!")
		os.Exit(1)
	}
	
	// Проверяем фронтенд (ИЗМЕНЕНО: папка frontend)
	if _, err := os.Stat(filepath.Join(projectDir, "frontend", "package.json")); os.IsNotExist(err) {
		fmt.Println("\n[ERROR] Не найдена папка 'frontend' или файл 'package.json' внутри неё!")
		fmt.Println("Убедитесь, что исходный код фронтенда лежит в папке 'frontend'.")
		os.Exit(1)
	}
}

func ensureLockFile(projectDir string) {
	backendDir := filepath.Join(projectDir, "backend_core")
	lockFile := filepath.Join(backendDir, "uv.lock")
	pyprojectFile := filepath.Join(backendDir, "pyproject.toml")

	if _, err := os.Stat(lockFile); err == nil {
		return
	}
	
	if _, err := os.Stat(pyprojectFile); os.IsNotExist(err) {
		return
	}

	fmt.Println("\n[WARN] Файл uv.lock не найден. Генерируем автоматически...")
	fmt.Println("[INFO] Это может занять около минуты...")

	err := runCmd(projectDir, "docker", "run", "--rm",
		"-v", fmt.Sprintf("%s:/app", backendDir),
		"-w", "/app",
		"-e", "UV_PROJECT_ENVIRONMENT=/tmp/uv-venv",
		"python:3.12-slim",
		"sh", "-c", "pip install --quiet uv==0.5.11 && uv lock")

	if err != nil {
		fmt.Println("\n[ERROR] Не удалось сгенерировать uv.lock.")
		fmt.Println("Убедитесь, что Docker имеет доступ к интернету.")
		os.Exit(1)
	}
	fmt.Println("[OK] uv.lock успешно создан.")
}

func setupCompose(projectDir string) {
	composePath := filepath.Join(projectDir, "docker-compose.yml")
	templatePath := filepath.Join(projectDir, "templates", "docker-compose.yml")

	if _, err := os.Stat(composePath); err == nil {
		fmt.Println("[INFO] Файл docker-compose.yml уже существует.")
		return
	}

	fmt.Println("[INFO] Создание docker-compose.yml из шаблона...")
	
	srcFile, err := os.Open(templatePath)
	if err != nil {
		fmt.Printf("\n[ERROR] Не найден шаблон: %s\n", templatePath)
		os.Exit(1)
	}
	defer srcFile.Close()

	dstFile, err := os.Create(composePath)
	if err != nil {
		fmt.Printf("\n[ERROR] Не удалось создать %s\n", composePath)
		os.Exit(1)
	}
	defer dstFile.Close()

	_, err = io.Copy(dstFile, srcFile)
	if err != nil {
		fmt.Println("[ERROR] Ошибка при копировании файла.")
		os.Exit(1)
	}
	fmt.Println("[OK] docker-compose.yml создан.")
}

func setupEnv(projectDir string) {
	envPath := filepath.Join(projectDir, ".env")
	examplePath := filepath.Join(projectDir, "templates", ".env.example")

	if _, err := os.Stat(envPath); err == nil {
		fmt.Println("[INFO] Файл .env уже существует. Используем текущие настройки.")
		return
	}

	fmt.Println("[INFO] Создание нового .env с безопасным паролем...")
	password := generatePassword(24)
	
	content, err := os.ReadFile(examplePath)
	if err != nil {
		fmt.Printf("\n[ERROR] Не найден шаблон: %s\n", examplePath)
		os.Exit(1)
	}

	newContent := strings.Replace(string(content), "DB_PASSWORD=CHANGE_ME", "DB_PASSWORD="+password, 1)
	os.WriteFile(envPath, []byte(newContent), 0644)
	fmt.Println("[OK] Файл .env создан в корне проекта.")
}

func main() {
	fmt.Println("==================================================")
	fmt.Println("  ConturAI Core - Установщик (v3.0)")
	fmt.Println("==================================================")

	if err := runCmd(".", "docker", "info"); err != nil {
		fmt.Println("\n[ERROR] Docker не запущен.")
		os.Exit(1)
	}

	projectDir := findProjectRoot()
	fmt.Printf("[INFO] Рабочая директория: %s\n", projectDir)

	checkProjectStructure(projectDir)

	ensureLockFile(projectDir)
	setupEnv(projectDir)
	setupCompose(projectDir)

	// 1. Собираем образы
	fmt.Println("\n[INFO] Сборка Docker-образов (Бэкенд + Фронтенд)...")
	fmt.Println("[INFO] Первая сборка может занять несколько минут...")
	if !dc(projectDir, "build") {
		os.Exit(1)
	}

	// 2. Запускаем ТОЛЬКО базу данных
	fmt.Println("\n[INFO] Запуск Базы Данных...")
	dc(projectDir, "up", "-d", "postgres")

	fmt.Println("[INFO] Ожидание запуска базы данных (10 секунд)...")
	time.Sleep(10 * time.Second)

	// 3. Инициализируем БД
	fmt.Println("\n[INFO] Создание таблиц и администратора...")
	runCmd(projectDir, "docker", "compose", "run", "--rm", "backend", "python", "scripts/manage.py", "init-db")
	runCmd(projectDir, "docker", "compose", "run", "--rm", "backend", "python", "scripts/manage.py", "reset-admin")

	// 4. Запускаем всё остальное
	fmt.Println("\n[INFO] Запуск Бэкенда и Фронтенда...")
	if !dc(projectDir, "up", "-d") {
		os.Exit(1)
	}

	fmt.Println("\n==================================================")
	fmt.Println("  УСТАНОВКА ЗАВЕРШЕНА!")
	fmt.Println("  Веб-интерфейс: http://localhost:3000")
	fmt.Println("  Swagger API:   http://localhost:8000/docs")
	fmt.Println("==================================================")
	
	reader := bufio.NewReader(os.Stdin)
	fmt.Println("Нажмите Enter для выхода...")
	reader.ReadString('\n')
}