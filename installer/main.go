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

// ==============================================================================
// УТИЛИТЫ
// ==============================================================================

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

	// 1. Если exe в корне
	if _, err := os.Stat(filepath.Join(dir, "templates")); err == nil {
		return dir
	}
	// 2. Если exe в папке bin
	parentDir := filepath.Dir(dir)
	if _, err := os.Stat(filepath.Join(parentDir, "templates")); err == nil {
		return parentDir
	}
	// 3. Если запущен из текущей директории
	currentDir, _ := os.Getwd()
	if _, err := os.Stat(filepath.Join(currentDir, "templates")); err == nil {
		return currentDir
	}
	return dir
}

func checkProjectStructure(projectDir string) {
	if _, err := os.Stat(filepath.Join(projectDir, "backend", "pyproject.toml")); os.IsNotExist(err) {
		fmt.Println("\n[ERROR] Не найдена папка 'backend' или файл 'pyproject.toml'!")
		os.Exit(1)
	}
	if _, err := os.Stat(filepath.Join(projectDir, "frontend", "package.json")); os.IsNotExist(err) {
		fmt.Println("\n[ERROR] Не найдена папка 'frontend' или файл 'package.json'!")
		os.Exit(1)
	}
}

func ensureLockFile(projectDir string) {
	backendDir := filepath.Join(projectDir, "backend")
	lockFile := filepath.Join(backendDir, "uv.lock")
	if _, err := os.Stat(lockFile); err == nil {
		return
	}

	fmt.Println("\n[WARN] Файл uv.lock не найден. Генерируем автоматически...")
	err := runCmd(projectDir, "docker", "run", "--rm",
		"-v", fmt.Sprintf("%s:/app", backendDir),
		"-w", "/app",
		"-e", "UV_PROJECT_ENVIRONMENT=/tmp/uv-venv",
		"python:3.12-slim",
		"sh", "-c", "pip install --quiet uv==0.5.11 && uv lock")

	if err != nil {
		fmt.Println("\n[ERROR] Не удалось сгенерировать uv.lock.")
		os.Exit(1)
	}
	fmt.Println("[OK] uv.lock успешно создан.")
}

func setupEnv(projectDir string, force bool) {
	envPath := filepath.Join(projectDir, ".env")
	examplePath := filepath.Join(projectDir, "templates", ".env.example")

	if !force {
		if _, err := os.Stat(envPath); err == nil {
			fmt.Println("[INFO] Файл .env уже существует. Используем текущие настройки.")
			return
		}
	}

	fmt.Println("[INFO] Создание нового .env...")
	password := generatePassword(24)
	content, err := os.ReadFile(examplePath)
	if err != nil {
		fmt.Printf("\n[ERROR] Не найден шаблон: %s\n", examplePath)
		os.Exit(1)
	}

	newContent := strings.Replace(string(content), "DB_PASSWORD=CHANGE_ME", "DB_PASSWORD="+password, 1)
	os.WriteFile(envPath, []byte(newContent), 0644)
	fmt.Println("[OK] Файл .env создан.")
}

func setupCompose(projectDir string) {
	composePath := filepath.Join(projectDir, "docker-compose.yml")
	templatePath := filepath.Join(projectDir, "templates", "docker-compose.yml")

	if _, err := os.Stat(composePath); err == nil {
		return // Уже есть
	}

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

	io.Copy(dstFile, srcFile)
	fmt.Println("[OK] docker-compose.yml создан.")
}

// ==============================================================================
// БИЗНЕС-ЛОГИКА (УСТАНОВКА, ОБНОВЛЕНИЕ, ПЕРЕУСТАНОВКА)
// ==============================================================================

func doInstall(projectDir string) {
	fmt.Println("\n--- НАЧАЛО УСТАНОВКИ ---")
	ensureLockFile(projectDir)
	setupEnv(projectDir, false)
	setupCompose(projectDir)

	fmt.Println("\n[INFO] Сборка Docker-образов (это может занять время)...")
	if !dc(projectDir, "build") {
		return
	}

	fmt.Println("\n[INFO] Запуск Базы Данных...")
	dc(projectDir, "up", "-d", "postgres")

	fmt.Println("[INFO] Ожидание запуска базы данных (10 секунд)...")
	time.Sleep(10 * time.Second)

	fmt.Println("\n[INFO] Инициализация БД и создание администратора...")
	dc(projectDir, "run", "--rm", "backend", "python", "scripts/manage.py", "init-db")
	dc(projectDir, "run", "--rm", "backend", "python", "scripts/manage.py", "reset-admin")

	fmt.Println("\n[INFO] Запуск всех сервисов...")
	if !dc(projectDir, "up", "-d") {
		return
	}

	fmt.Println("\n==================================================")
	fmt.Println("  УСТАНОВКА ЗАВЕРШЕНА!")
	fmt.Println("  Веб-интерфейс: http://localhost:3000")
	fmt.Println("  Swagger API:   http://localhost:8000/docs")
	fmt.Println("==================================================")
}

func doUpdate(projectDir string) {
	fmt.Println("\n--- ОБНОВЛЕНИЕ (сохранение данных) ---")
	if _, err := os.Stat(filepath.Join(projectDir, ".env")); os.IsNotExist(err) {
		fmt.Println("[ERROR] Файл .env не найден. Сначала выполните Установку.")
		return
	}

	ensureLockFile(projectDir)

	fmt.Println("\n[INFO] Пересборка контейнеров...")
	dc(projectDir, "down", "--remove-orphans")
	dc(projectDir, "build")
	dc(projectDir, "up", "-d", "postgres")

	fmt.Println("[INFO] Ожидание БД (10 секунд)...")
	time.Sleep(10 * time.Second)

	fmt.Println("\n[INFO] Применение миграций БД...")
	dc(projectDir, "run", "--rm", "backend", "python", "scripts/manage.py", "migrate")

	fmt.Println("\n[INFO] Запуск всех сервисов...")
	dc(projectDir, "up", "-d")

	fmt.Println("\n[SUCCESS] Обновление завершено! Сервисы перезапущены.")
}

func doReinstall(projectDir string) {
	fmt.Println("\n--- ПОЛНАЯ ПЕРЕУСТАНОВКА (СБРОС БД) ---")
	fmt.Print("ВНИМАНИЕ! Это удалит все данные, БД и .env. Продолжить? (y/N): ")
	
	reader := bufio.NewReader(os.Stdin)
	confirm, _ := reader.ReadString('\n')
	if strings.ToLower(strings.TrimSpace(confirm)) != "y" {
		fmt.Println("Отменено.")
		return
	}

	fmt.Println("\n[INFO] Удаление контейнеров и томов...")
	dc(projectDir, "down", "-v", "--remove-orphans")

	fmt.Println("[INFO] Удаление .env...")
	os.Remove(filepath.Join(projectDir, ".env"))

	doInstall(projectDir)
}

// ==============================================================================
// МЕНЮ MANAGER.PY
// ==============================================================================

func menuManage(projectDir string) {
	reader := bufio.NewReader(os.Stdin)
	for {
		fmt.Println("\n--- Команды manage.py ---")
		fmt.Println("  1) init-db (Создать таблицы)")
		fmt.Println("  2) reset-admin (Сбросить пароль админа)")
		fmt.Println("  3) migrate (Применить миграции)")
		fmt.Println("  0) Назад в главное меню")
		fmt.Print("Номер [0]: ")

		choice, _ := reader.ReadString('\n')
		choice = strings.TrimSpace(choice)

		switch choice {
		case "1":
			dc(projectDir, "run", "--rm", "backend", "python", "scripts/manage.py", "init-db")
		case "2":
			dc(projectDir, "run", "--rm", "backend", "python", "scripts/manage.py", "reset-admin")
		case "3":
			dc(projectDir, "run", "--rm", "backend", "python", "scripts/manage.py", "migrate")
		case "0":
			return
		default:
			fmt.Println("Неверный выбор.")
		}
	}
}

// ==============================================================================
// ГЛАВНОЕ МЕНЮ
// ==============================================================================

func main() {
	fmt.Println("==================================================")
	fmt.Println("  ConturAI Core - Установщик (v3.0)")
	fmt.Println("==================================================")

	if err := runCmd(".", "docker", "info"); err != nil {
		fmt.Println("\n[ERROR] Docker не запущен.")
		os.Exit(1)
	}

	projectDir := findProjectRoot()
	checkProjectStructure(projectDir)
	fmt.Printf("[INFO] Рабочая директория: %s\n", projectDir)

	reader := bufio.NewReader(os.Stdin)

	for {
		fmt.Println("\nГлавное меню:")
		fmt.Println("  1) Установка с нуля")
		fmt.Println("  2) Обновление (сохранить данные)")
		fmt.Println("  3) Полная переустановка (сброс БД)")
		fmt.Println("  4) Команды manage.py")
		fmt.Println("  0) Выход")
		fmt.Print("Номер [1]: ")

		choice, _ := reader.ReadString('\n')
		choice = strings.TrimSpace(choice)
		if choice == "" {
			choice = "1"
		}

		switch choice {
		case "1":
			doInstall(projectDir)
		case "2":
			doUpdate(projectDir)
		case "3":
			doReinstall(projectDir)
		case "4":
			menuManage(projectDir)
		case "0":
			fmt.Println("До свидания!")
			os.Exit(0)
		default:
			fmt.Println("Неверный выбор.")
		}
	}
}